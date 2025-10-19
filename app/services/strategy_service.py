from datetime import datetime
from typing import List, Optional

from app.models.strategy import (
    Strategy,
    StrategyCreate,
    StrategySubscriptionCreate,
    StrategySubscriptionResponse,
    StrategyUpdate,
)
from app.repositories.strategy_repository import StrategyRepository


class StrategyService:
    def __init__(self, repository: Optional[StrategyRepository] = None) -> None:
        self.repository = repository or StrategyRepository()

    async def create_strategy(
        self, strategy_create: StrategyCreate, user_id: str
    ) -> Strategy:
        payload = strategy_create.dict()
        now = datetime.utcnow()
        payload.update({"user_id": user_id, "created_at": now, "updated_at": now})

        strategy_id = await self.repository.insert_strategy(payload)
        return await self.get_strategy_by_id(strategy_id)

    async def get_strategy_by_id(self, strategy_id: str) -> Optional[Strategy]:
        document = await self.repository.find_by_id(strategy_id)
        return self._document_to_strategy(document) if document else None

    async def get_strategies_by_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = await self.repository.list_by_user(user_id, skip, limit)
        async for document in cursor:
            strategies.append(self._document_to_strategy(document))
        return strategies

    async def get_public_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = await self.repository.list_public(skip, limit)
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
        if not await self.repository.update_strategy(strategy_id, update_data):
            return None
        return await self.get_strategy_by_id(strategy_id)

    async def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy or strategy.user_id != user_id:
            return False

        return await self.repository.delete_strategy(strategy_id)

    async def subscribe_strategy(
        self, subscription_create: StrategySubscriptionCreate, user_id: str
    ) -> StrategySubscriptionResponse:
        strategy = await self.get_strategy_by_id(subscription_create.strategy_id)
        if not strategy:
            raise ValueError("策略不存在")

        exists = await self.repository.find_subscription(
            user_id, subscription_create.strategy_id
        )
        if exists:
            raise ValueError("已经订阅该策略")

        payload = {
            "user_id": user_id,
            "strategy_id": subscription_create.strategy_id,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        subscription_id = await self.repository.insert_subscription(payload)
        subscription = await self.repository.find_subscription_by_id(subscription_id)
        return self._document_to_subscription(subscription, strategy)

    async def unsubscribe_strategy(self, strategy_id: str, user_id: str) -> bool:
        return await self.repository.delete_subscription(user_id, strategy_id)

    async def get_user_subscriptions(
        self, user_id: str
    ) -> List[StrategySubscriptionResponse]:
        subscriptions: List[StrategySubscriptionResponse] = []
        cursor = await self.repository.list_subscriptions(user_id)
        async for document in cursor:
            strategy = await self.get_strategy_by_id(document["strategy_id"])
            subscriptions.append(self._document_to_subscription(document, strategy))
        return subscriptions

    async def get_all_strategies(
        self, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        strategies: List[Strategy] = []
        cursor = await self.repository.list_all(skip, limit)
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
