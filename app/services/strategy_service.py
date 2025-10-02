from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.db import mongodb
from app.models.strategy import (
    Strategy,
    StrategyCreate,
    StrategyInDB,
    StrategySubscription,
    StrategySubscriptionAdminCreate,
    StrategySubscriptionCreate,
    StrategySubscriptionResponse,
    StrategySubscriptionUpdate,
    StrategyUpdate,
)


class StrategyService:
    def __init__(self) -> None:
        self.collection = mongodb.db.strategies
        self.subscription_collection = mongodb.db.strategy_subscriptions

    async def create_strategy(self, strategy_create: StrategyCreate, user_id: int) -> Strategy:
        """创建策略"""

        strategy_dict = strategy_create.dict()
        now = datetime.utcnow()
        strategy_dict["user_id"] = user_id
        strategy_dict["created_at"] = now
        strategy_dict["updated_at"] = now
        strategy_dict.setdefault("source", "internal")
        strategy_dict.setdefault("metadata", {})
        strategy_dict.setdefault("external_id", None)

        strategy_in_db = StrategyInDB(**strategy_dict)
        result = await self.collection.insert_one(strategy_in_db.dict(by_alias=True))
        return await self.get_strategy_by_id(str(result.inserted_id))

    async def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        """根据ID获取策略"""

        document = await self._find_one_by_id(strategy_id)
        return self._deserialize_strategy(document)

    async def get_strategy_by_external_id(
        self, external_id: str, source: str = "joinquant"
    ) -> Optional[Strategy]:
        """通过外部平台标识获取策略"""

        if not external_id:
            return None
        document = await self.collection.find_one(
            {"external_id": external_id, "source": source}
        )
        return self._deserialize_strategy(document)

    async def get_strategies_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """获取用户的策略列表"""

        cursor = (
            self.collection.find({"user_id": user_id})
            .skip(skip)
            .limit(limit)
            .sort("created_at", -1)
        )
        documents = await cursor.to_list(length=None)
        return [self._deserialize_strategy(doc) for doc in documents if doc]

    async def get_public_strategies(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取公开策略列表"""

        cursor = (
            self.collection.find({"is_public": True, "is_active": True})
            .skip(skip)
            .limit(limit)
            .sort("created_at", -1)
        )
        documents = await cursor.to_list(length=None)
        return [self._deserialize_strategy(doc) for doc in documents if doc]

    async def update_strategy(
        self, strategy_id: str, strategy_update: StrategyUpdate, user_id: int
    ) -> Optional[Strategy]:
        """更新策略"""

        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return None

        update_data = strategy_update.dict(exclude_unset=True)
        if not update_data:
            return strategy

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(strategy_id)}, {"$set": update_data}
        )
        return await self.get_strategy_by_id(strategy_id)

    async def delete_strategy(self, strategy_id: str, user_id: int) -> bool:
        """删除策略"""

        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return False

        result = await self.collection.delete_one({"_id": ObjectId(strategy_id)})
        return result.deleted_count > 0

    async def subscribe_strategy(
        self, subscription_create: StrategySubscriptionCreate, user_id: int
    ) -> StrategySubscriptionResponse:
        """订阅策略"""

        strategy = await self.get_strategy_by_id(subscription_create.strategy_id)
        if not strategy:
            raise ValueError("策略不存在")
        if not strategy.is_active:
            raise ValueError("策略已被停用")

        existing = await self.subscription_collection.find_one(
            {"strategy_id": subscription_create.strategy_id, "user_id": user_id}
        )
        if existing:
            if existing.get("is_active", True):
                raise ValueError("已经订阅该策略")
            await self.subscription_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_active": True, "updated_at": datetime.utcnow()}},
            )
            refreshed = await self.subscription_collection.find_one(
                {"_id": existing["_id"]}
            )
            return await self._build_subscription_response(refreshed, strategy=strategy)

        now = datetime.utcnow()
        subscription_dict = {
            "strategy_id": subscription_create.strategy_id,
            "user_id": user_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        subscription = StrategySubscription(**subscription_dict)
        result = await self.subscription_collection.insert_one(subscription.dict(by_alias=True))
        document = await self.subscription_collection.find_one({"_id": result.inserted_id})
        return await self._build_subscription_response(document, strategy=strategy)

    async def unsubscribe_strategy(self, strategy_id: str, user_id: int) -> bool:
        """取消订阅策略"""

        result = await self.subscription_collection.update_one(
            {"strategy_id": strategy_id, "user_id": user_id, "is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def get_user_subscriptions(
        self, user_id: int
    ) -> List[StrategySubscriptionResponse]:
        """获取用户的策略订阅列表"""

        cursor = (
            self.subscription_collection.find({"user_id": user_id})
            .sort("created_at", -1)
        )
        subscriptions: List[StrategySubscriptionResponse] = []
        async for document in cursor:
            subscriptions.append(await self._build_subscription_response(document))
        return subscriptions

    async def get_all_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """获取所有策略（管理员功能）"""

        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        documents = await cursor.to_list(length=None)
        return [self._deserialize_strategy(doc) for doc in documents if doc]

    async def get_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        strategy_id: Optional[str] = None,
        user_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> List[StrategySubscriptionResponse]:
        """管理员获取订阅列表"""

        query: Dict[str, Any] = {}
        if strategy_id:
            query["strategy_id"] = strategy_id
        if user_id is not None:
            query["user_id"] = user_id
        if is_active is not None:
            query["is_active"] = is_active

        cursor = (
            self.subscription_collection.find(query)
            .skip(skip)
            .limit(limit)
            .sort("created_at", -1)
        )
        subscriptions: List[StrategySubscriptionResponse] = []
        async for document in cursor:
            subscriptions.append(await self._build_subscription_response(document))
        return subscriptions

    async def update_subscription(
        self, subscription_id: str, update: StrategySubscriptionUpdate
    ) -> Optional[StrategySubscriptionResponse]:
        """管理员更新订阅状态"""

        try:
            oid = ObjectId(subscription_id)
        except (InvalidId, TypeError):
            return None

        payload = update.dict(exclude_unset=True)
        if payload:
            payload["updated_at"] = datetime.utcnow()
            result = await self.subscription_collection.update_one(
                {"_id": oid}, {"$set": payload}
            )
            if result.matched_count == 0:
                return None

        document = await self.subscription_collection.find_one({"_id": oid})
        if not document:
            return None
        return await self._build_subscription_response(document)

    async def admin_create_subscription(
        self, payload: StrategySubscriptionAdminCreate
    ) -> StrategySubscriptionResponse:
        """管理员直接创建或激活订阅"""

        strategy = await self.get_strategy_by_id(payload.strategy_id)
        if not strategy:
            raise ValueError("策略不存在")

        existing = await self.subscription_collection.find_one(
            {"strategy_id": payload.strategy_id, "user_id": payload.user_id}
        )
        if existing:
            if existing.get("is_active", True):
                raise ValueError("订阅已存在")
            await self.subscription_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_active": True, "updated_at": datetime.utcnow()}},
            )
            refreshed = await self.subscription_collection.find_one(
                {"_id": existing["_id"]}
            )
            return await self._build_subscription_response(refreshed, strategy=strategy)

        now = datetime.utcnow()
        document = {
            "strategy_id": payload.strategy_id,
            "user_id": payload.user_id,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.subscription_collection.insert_one(document)
        created = await self.subscription_collection.find_one({"_id": result.inserted_id})
        return await self._build_subscription_response(created, strategy=strategy)

    async def get_subscription_by_id(
        self, subscription_id: str
    ) -> Optional[StrategySubscriptionResponse]:
        try:
            oid = ObjectId(subscription_id)
        except (InvalidId, TypeError):
            return None

        document = await self.subscription_collection.find_one({"_id": oid})
        if not document:
            return None
        return await self._build_subscription_response(document)

    async def user_has_access_to_strategy(
        self, strategy_id: str, user_id: int, *, include_public: bool = True
    ) -> bool:
        """判断用户是否可以访问指定策略"""

        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or not strategy.is_active:
            return False

        if strategy.user_id == user_id:
            return True

        if include_public and strategy.is_public:
            return True

        subscription = await self.subscription_collection.find_one(
            {"strategy_id": strategy_id, "user_id": user_id, "is_active": True}
        )
        return subscription is not None

    async def _find_one_by_id(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        try:
            oid = ObjectId(strategy_id)
        except (InvalidId, TypeError):
            return None
        return await self.collection.find_one({"_id": oid})

    def _deserialize_strategy(
        self, strategy_doc: Optional[Dict[str, Any]]
    ) -> Optional[Strategy]:
        if not strategy_doc:
            return None

        document = dict(strategy_doc)
        document["id"] = str(document.pop("_id"))
        document.setdefault("parameters", {})
        document.setdefault("metadata", {})
        document.setdefault("source", "internal")
        document.setdefault("external_id", None)
        document.setdefault("is_public", False)
        document.setdefault("is_active", True)
        document.setdefault("last_signal_at", None)
        document.setdefault("last_positions_at", None)
        return Strategy(**document)

    async def _build_subscription_response(
        self,
        subscription_doc: Optional[Dict[str, Any]],
        *,
        strategy: Optional[Strategy] = None,
    ) -> StrategySubscriptionResponse:
        if not subscription_doc:
            raise ValueError("订阅记录不存在")

        document = dict(subscription_doc)
        document["id"] = str(document.pop("_id"))
        document.setdefault("updated_at", document.get("created_at", datetime.utcnow()))
        if strategy is None:
            strategy = await self.get_strategy_by_id(document["strategy_id"])
        return StrategySubscriptionResponse(**document, strategy=strategy)
