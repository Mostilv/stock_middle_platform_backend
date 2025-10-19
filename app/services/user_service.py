from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from app.core.security import get_password_hash, verify_password
from app.db import mongodb
from app.models.user import User, UserCreate, UserInDB, UserUpdate


class UserService:
    def __init__(self) -> None:
        self.collection = mongodb.db.users

    async def create_user(self, user_create: UserCreate) -> User:
        if await self.collection.find_one({"username": user_create.username}):
            raise ValueError("用户名已存在")

        if await self.collection.find_one({"email": user_create.email}):
            raise ValueError("邮箱已存在")

        now = datetime.utcnow()
        user_data = user_create.dict(exclude={"password"})
        user_doc = UserInDB(
            **user_data,
            hashed_password=get_password_hash(user_create.password),
            created_at=now,
            updated_at=now,
        )

        insert_result = await self.collection.insert_one(
            user_doc.dict(by_alias=True, exclude_none=True)
        )
        return await self.get_user_by_id(str(insert_result.inserted_id))

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None
        document = await self.collection.find_one({"_id": ObjectId(user_id)})
        return self._document_to_user(document) if document else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        document = await self.collection.find_one({"username": username})
        return self._document_to_user(document) if document else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        document = await self.collection.find_one({"email": email})
        return self._document_to_user(document) if document else None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        document = await self.collection.find_one({"username": username})
        if not document:
            return None

        user_in_db = UserInDB(**document)
        if not verify_password(password, user_in_db.hashed_password):
            return None

        return self._document_to_user(document)

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None

        update_data = user_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_user_by_id(user_id)

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
        )
        return await self.get_user_by_id(user_id)

    async def add_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {"roles": {"$each": roles}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return await self.get_user_by_id(user_id)

    async def remove_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {"roles": {"$in": roles}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return await self.get_user_by_id(user_id)

    async def add_permissions(self, user_id: str, permissions: List[str]) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$addToSet": {"permissions": {"$each": permissions}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return await self.get_user_by_id(user_id)

    async def remove_permissions(
        self, user_id: str, permissions: List[str]
    ) -> Optional[User]:
        if not ObjectId.is_valid(user_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {"permissions": {"$in": permissions}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> bool:
        if not ObjectId.is_valid(user_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        users: List[User] = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for document in cursor:
            users.append(self._document_to_user(document))
        return users

    async def create_superuser(
        self, username: str, email: str, password: str, full_name: Optional[str] = None
    ) -> User:
        user = await self.create_user(
            UserCreate(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                roles=["admin"],
                permissions=[],
                is_superuser=True,
            )
        )

        await self.collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": {"is_superuser": True, "updated_at": datetime.utcnow()}},
        )
        return await self.get_user_by_id(user.id)

    @staticmethod
    def _document_to_user(document: dict) -> User:
        document = {**document, "id": str(document["_id"])}
        document.setdefault("roles", [])
        document.setdefault("permissions", [])
        return User(**document)
