from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.db import mongodb
from app.models.role import Role, RoleCreate, RoleUpdate


class RoleService:
    def __init__(self) -> None:
        self.collection = mongodb.db.roles

    async def create_role(self, role_create: RoleCreate) -> Role:
        if await self.collection.find_one({"name": role_create.name}):
            raise ValueError("角色已存在")

        now = datetime.utcnow()
        role_doc = {
            "name": role_create.name,
            "description": role_create.description,
            "permissions": role_create.permissions,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(role_doc)
        return await self.get_role_by_id(str(result.inserted_id))

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        if not ObjectId.is_valid(role_id):
            return None
        document = await self.collection.find_one({"_id": ObjectId(role_id)})
        return self._document_to_role(document) if document else None

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        document = await self.collection.find_one({"name": name})
        return self._document_to_role(document) if document else None

    async def list_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        roles: List[Role] = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for document in cursor:
            roles.append(self._document_to_role(document))
        return roles

    async def update_role(self, role_id: str, role_update: RoleUpdate) -> Optional[Role]:
        if not ObjectId.is_valid(role_id):
            return None

        update_data = role_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_role_by_id(role_id)

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(role_id)},
            {"$set": update_data},
        )
        return await self.get_role_by_id(role_id)

    async def delete_role(self, role_id: str) -> bool:
        if not ObjectId.is_valid(role_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(role_id)})
        return result.deleted_count > 0

    @staticmethod
    def _document_to_role(document: dict) -> Role:
        return Role(
            id=str(document["_id"]),
            name=document["name"],
            description=document.get("description"),
            permissions=document.get("permissions", []),
            created_at=document.get("created_at", datetime.utcnow()),
            updated_at=document.get("updated_at", datetime.utcnow()),
        )
