"""
MongoDB persistence helpers for strategies and subscriptions.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId

from .base import BaseRepository


class StrategyRepository(BaseRepository):
    collection_name = "strategies"

    def __init__(self) -> None:
        super().__init__()
        self.subscription_collection = self.collection.database["strategy_subscriptions"]

    async def find_by_id(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(strategy_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(strategy_id)})

    async def insert_strategy(self, document: Dict[str, Any]) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def list_by_user(self, user_id: str, skip: int, limit: int):
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        return cursor

    async def list_public(self, skip: int, limit: int):
        cursor = (
            self.collection.find({"is_public": True, "is_active": True})
            .skip(skip)
            .limit(limit)
        )
        return cursor

    async def list_all(self, skip: int, limit: int):
        cursor = self.collection.find().skip(skip).limit(limit)
        return cursor

    async def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> bool:
        if not ObjectId.is_valid(strategy_id):
            return False
        await self.collection.update_one(
            {"_id": ObjectId(strategy_id)},
            {"$set": updates},
        )
        return True

    async def delete_strategy(self, strategy_id: str) -> bool:
        if not ObjectId.is_valid(strategy_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(strategy_id)})
        return result.deleted_count > 0

    async def find_subscription(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(strategy_id):
            return None
        return await self.subscription_collection.find_one(
            {"user_id": user_id, "strategy_id": strategy_id}
        )

    async def insert_subscription(self, document: Dict[str, Any]) -> str:
        result = await self.subscription_collection.insert_one(document)
        return str(result.inserted_id)

    async def find_subscription_by_id(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(subscription_id):
            return None
        return await self.subscription_collection.find_one({"_id": ObjectId(subscription_id)})

    async def delete_subscription(self, user_id: str, strategy_id: str) -> bool:
        result = await self.subscription_collection.delete_one(
            {"user_id": user_id, "strategy_id": strategy_id}
        )
        return result.deleted_count > 0

    async def list_subscriptions(self, user_id: str):
        cursor = self.subscription_collection.find({"user_id": user_id})
        return cursor
