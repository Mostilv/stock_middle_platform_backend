"""
MongoDB persistence helpers for user entities.
"""

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from bson import ObjectId

from .base import BaseRepository


class UserRepository(BaseRepository):
    collection_name = "users"

    async def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"username": username})

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"email": email})

    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(user_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(user_id)})

    async def insert_user(self, document: Dict[str, Any]) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
        )
        return True

    async def delete_user(self, user_id: str) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def list_users(self, skip: int, limit: int):
        cursor = self.collection.find().skip(skip).limit(limit)
        return cursor

    async def add_to_set(self, user_id: str, field: str, values: Iterable[str]) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        now = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {field: {"$each": list(values)}},
                "$set": {"updated_at": now},
            },
        )
        return True

    async def pull_from_set(self, user_id: str, field: str, values: Iterable[str]) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        now = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {field: {"$in": list(values)}},
                "$set": {"updated_at": now},
            },
        )
        return True

