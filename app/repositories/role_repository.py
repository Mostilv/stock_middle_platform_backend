"""
MongoDB persistence helpers for role entities.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId

from .base import BaseRepository


class RoleRepository(BaseRepository):
    collection_name = "roles"

    async def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"name": name})

    async def find_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(role_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(role_id)})

    async def insert_role(self, document: Dict[str, Any]) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_role(self, role_id: str, updates: Dict[str, Any]) -> bool:
        if not ObjectId.is_valid(role_id):
            return False
        await self.collection.update_one(
            {"_id": ObjectId(role_id)},
            {"$set": updates},
        )
        return True

    async def delete_role(self, role_id: str) -> bool:
        if not ObjectId.is_valid(role_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(role_id)})
        return result.deleted_count > 0

    async def list_roles(self, skip: int, limit: int):
        cursor = self.collection.find().skip(skip).limit(limit)
        return cursor
