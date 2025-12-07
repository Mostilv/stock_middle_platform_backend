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
        user_data.setdefault("display_name", user_create.username)
        user_data.setdefault("avatar_url", self._default_avatar(user_create.username))
        user_data.setdefault("remark", "")
        user_data.setdefault("isReal", True)
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

        if "username" in update_data:
            existing = await self.repository.find_by_username(update_data["username"])
            if existing and str(existing.get("_id")) != user_id:
                raise ValueError("用户名已存在")

        if "email" in update_data:
            existing_email = await self.repository.find_by_email(update_data["email"])
            if existing_email and str(existing_email.get("_id")) != user_id:
                raise ValueError("邮箱已存在")

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(
                update_data.pop("password")
            )

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

    async def ensure_default_admin(self) -> User:
        """Ensure a demo admin user exists for the front-end integration."""
        default_password = "123456"
        existing = await self.repository.find_by_username("admin")
        now = datetime.utcnow()

        if existing:
            await self.repository.update_user(
                str(existing["_id"]),
                {
                    "email": existing.get("email") or "admin@example.com",
                    "display_name": existing.get("display_name") or "系统管理员",
                    "avatar_url": existing.get("avatar_url")
                    or self._default_avatar("admin"),
                    "remark": existing.get("remark") or "系统默认管理员",
                    "is_superuser": True,
                    "roles": list(set(existing.get("roles") or []) | {"admin"}),
                    "hashed_password": get_password_hash(default_password),
                    "updated_at": now,
                },
            )
            refreshed = await self.get_user_by_username("admin")
            if refreshed:
                return refreshed

        return await self.create_superuser(
            username="admin",
            email="admin@example.com",
            password=default_password,
            full_name="系统管理员",
        )

    @staticmethod
    def _document_to_user(document: dict) -> User:
        document = {**document, "id": str(document["_id"])}
        document.setdefault("roles", [])
        document.setdefault("permissions", [])
        document.setdefault("display_name", document.get("username"))
        document.setdefault("avatar_url", UserService._default_avatar(document["username"]))
        document.setdefault("remark", "")
        document.setdefault("isReal", True)
        return User(**document)

    @staticmethod
    def _normalize_document(document: dict) -> dict:
        normalized = dict(document)
        if "_id" in normalized and not isinstance(normalized["_id"], str):
            normalized["_id"] = str(normalized["_id"])
        return normalized

    @staticmethod
    def _default_avatar(username: str) -> str:
        return f"https://api.dicebear.com/7.x/initials/svg?seed={username}"
