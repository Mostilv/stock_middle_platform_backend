from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.db import mongodb
from app.models.strategy import (
    Strategy,
    StrategyCreate,
    StrategySubscriptionCreate,
    StrategySubscriptionResponse,
    StrategyUpdate,
)


class StrategyService:
    def __init__(self) -> None:
        self.collection = mongodb.db.strategies
        self.subscription_collection = mongodb.db.strategy_subscriptions

    async def create_strategy(
        self, strategy_create: StrategyCreate, user_id: str
    ) -> Strategy:
        payload = strategy_create.dict()
        now = datetime.utcnow()
        payload.update({"user_id": user_id, "created_at": now, "updated_at": now})

        result = await self.collection.insert_one(payload)
        return await self.get_strategy_by_id(str(result.inserted_id))

    async def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        if not ObjectId.is_valid(strategy_id):
            return None

        document = await self.collection.find_one({"_id": ObjectId(strategy_id)})
        return self._document_to_strategy(document) if document else None

    async def get_strategies_by_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        async for document in cursor:
            strategies.append(self._document_to_strategy(document))
        return strategies

    async def get_public_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = (
            self.collection.find({"is_public": True, "is_active": True})
            .skip(skip)
            .limit(limit)
        )
        async for document in cursor:
            strategies.append(self._document_to_strategy(document))
        return strategies

    async def update_strategy(
        self, strategy_id: str, strategy_update: StrategyUpdate, user_id: str
    ) -> Optional[Strategy]:
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return None

        update_data = strategy_update.dict(exclude_unset=True)
        if not update_data:
            return strategy

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(strategy_id)},
            {"$set": update_data},
        )
        return await self.get_strategy_by_id(strategy_id)

    async def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return False

        result = await self.collection.delete_one({"_id": ObjectId(strategy_id)})
        return result.deleted_count > 0

    async def subscribe_strategy(
        self, subscription_create: StrategySubscriptionCreate, user_id: str
    ) -> StrategySubscriptionResponse:
        strategy = await self.get_strategy_by_id(subscription_create.strategy_id)
        if not strategy:
            raise ValueError("策略不存在")

        exists = await self.subscription_collection.find_one(
            {"user_id": user_id, "strategy_id": subscription_create.strategy_id}
        )
        if exists:
            raise ValueError("已经订阅该策略")

        payload = {
            "user_id": user_id,
            "strategy_id": subscription_create.strategy_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        result = await self.subscription_collection.insert_one(payload)
        subscription = await self.subscription_collection.find_one(
            {"_id": result.inserted_id}
        )
        return self._document_to_subscription(subscription, strategy)

    async def unsubscribe_strategy(self, strategy_id: str, user_id: str) -> bool:
        result = await self.subscription_collection.delete_one(
            {"user_id": user_id, "strategy_id": strategy_id}
        )
        return result.deleted_count > 0

    async def get_user_subscriptions(
        self, user_id: str
    ) -> List[StrategySubscriptionResponse]:
        subscriptions: List[StrategySubscriptionResponse] = []
        cursor = self.subscription_collection.find({"user_id": user_id})
        async for document in cursor:
            strategy = await self.get_strategy_by_id(document["strategy_id"])
            subscriptions.append(self._document_to_subscription(document, strategy))
        return subscriptions

    async def get_all_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for document in cursor:
            strategies.append(self._document_to_strategy(document))
        return strategies

    @staticmethod
    def _document_to_strategy(document: dict) -> Strategy:
        payload = {
            "id": str(document["_id"]),
            "name": document["name"],
            "description": document.get("description"),
            "user_id": document.get("user_id", ""),
            "is_public": document.get("is_public", False),
            "is_active": document.get("is_active", True),
            "strategy_type": document.get("strategy_type", ""),
            "parameters": document.get("parameters", {}),
            "created_at": document.get("created_at", datetime.utcnow()),
            "updated_at": document.get("updated_at", datetime.utcnow()),
        }
        return Strategy(**payload)

    def _document_to_subscription(
        self, document: dict, strategy: Optional[Strategy]
    ) -> StrategySubscriptionResponse:
        payload = {
            "id": str(document["_id"]),
            "user_id": document["user_id"],
            "strategy_id": document["strategy_id"],
            "is_active": document.get("is_active", True),
            "created_at": document.get("created_at", datetime.utcnow()),
            "strategy": strategy,
        }
        return StrategySubscriptionResponse(**payload)
