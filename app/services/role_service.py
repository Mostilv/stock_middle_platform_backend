from typing import List, Optional
from datetime import datetime
from app.db import mongodb
from app.models.role import RoleInDB, Role, RoleCreate, RoleUpdate
from bson import ObjectId


class RoleService:
    def __init__(self):
        self.collection = mongodb.db.roles

    async def create_role(self, role_create: RoleCreate) -> Role:
        existing = await self.get_role_by_name(role_create.name)
        if existing:
            raise ValueError("角色已存在")

        role_dict = role_create.dict()
        role_dict["created_at"] = datetime.now()
        role_dict["updated_at"] = datetime.now()

        role_in_db = RoleInDB(**role_dict)
        result = await self.collection.insert_one(role_in_db.dict(by_alias=True))
        return await self.get_role_by_id(str(result.inserted_id))

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        doc = await self.collection.find_one({"_id": ObjectId(role_id)})
        if doc:
            doc["id"] = str(doc["_id"])
            return Role(**doc)
        return None

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        doc = await self.collection.find_one({"name": name})
        if doc:
            doc["id"] = str(doc["_id"])
            return Role(**doc)
        return None

    async def list_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        roles: List[Role] = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            roles.append(Role(**doc))
        return roles

    async def update_role(self, role_id: str, role_update: RoleUpdate) -> Optional[Role]:
        update_data = role_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now()
            result = await self.collection.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return await self.get_role_by_id(role_id)
        return None

    async def delete_role(self, role_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(role_id)})
        return result.deleted_count > 0



