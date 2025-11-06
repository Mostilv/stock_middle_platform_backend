from datetime import datetime
from typing import List, Optional

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserCreate, UserInDB, UserUpdate
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: Optional[UserRepository] = None) -> None:
        self.repository = repository or UserRepository()

    async def create_user(self, user_create: UserCreate) -> User:
        if await self.repository.find_by_username(user_create.username):
            raise ValueError("用户名已存在")

        if await self.repository.find_by_email(user_create.email):
            raise ValueError("邮箱已存在")

        now = datetime.utcnow()
        user_data = user_create.dict(exclude={"password"})
        user_doc = UserInDB(
            **user_data,
            hashed_password=get_password_hash(user_create.password),
            created_at=now,
            updated_at=now,
        )

        user_id = await self.repository.insert_user(
            user_doc.dict(by_alias=True, exclude_none=True)
        )
        return await self.get_user_by_id(user_id)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        document = await self.repository.find_by_id(user_id)
        return self._document_to_user(document) if document else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        document = await self.repository.find_by_username(username)
        return self._document_to_user(document) if document else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        document = await self.repository.find_by_email(email)
        return self._document_to_user(document) if document else None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        document = await self.repository.find_by_username(username)
        if not document:
            return None

        user_in_db = UserInDB(**self._normalize_document(document))
        if not verify_password(password, user_in_db.hashed_password):
            return None

        return self._document_to_user(document)

    async def update_user(
        self, user_id: str, user_update: UserUpdate
    ) -> Optional[User]:
        update_data = user_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_user_by_id(user_id)

        update_data["updated_at"] = datetime.utcnow()
        if not await self.repository.update_user(user_id, update_data):
            return None
        return await self.get_user_by_id(user_id)

    async def add_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        if not await self.repository.add_to_set(user_id, "roles", roles):
            return None
        return await self.get_user_by_id(user_id)

    async def remove_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        if not await self.repository.pull_from_set(user_id, "roles", roles):
            return None
        return await self.get_user_by_id(user_id)

    async def add_permissions(
        self, user_id: str, permissions: List[str]
    ) -> Optional[User]:
        if not await self.repository.add_to_set(user_id, "permissions", permissions):
            return None
        return await self.get_user_by_id(user_id)

    async def remove_permissions(
        self, user_id: str, permissions: List[str]
    ) -> Optional[User]:
        if not await self.repository.pull_from_set(user_id, "permissions", permissions):
            return None
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> bool:
        return await self.repository.delete_user(user_id)

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        users: List[User] = []
        cursor = await self.repository.list_users(skip, limit)
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

        await self.repository.update_user(
            user.id,
            {"is_superuser": True, "updated_at": datetime.utcnow()},
        )
        return await self.get_user_by_id(user.id)

    @staticmethod
    def _document_to_user(document: dict) -> User:
        document = {**document, "id": str(document["_id"])}
        document.setdefault("roles", [])
        document.setdefault("permissions", [])
        return User(**document)

    @staticmethod
    def _normalize_document(document: dict) -> dict:
        normalized = dict(document)
        if "_id" in normalized and not isinstance(normalized["_id"], str):
            normalized["_id"] = str(normalized["_id"])
        return normalized
