import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.security import get_password_hash, verify_password
from app.db.database_utils import MySQLDataAccess
from app.models.user import User, UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """基于MySQL的用户管理服务"""

    _init_lock: asyncio.Lock = asyncio.Lock()
    _initialized: bool = False

    def __init__(self) -> None:
        self.users_table = "users"
        self.user_roles_table = "user_roles"
        self.user_permissions_table = "user_permissions"

    async def _ensure_tables(self) -> None:
        """确保用户相关表已在MySQL中创建"""

        if self.__class__._initialized:
            return

        async with self.__class__._init_lock:
            if self.__class__._initialized:
                return

            charset = settings.mysql_charset

            create_users = f"""
            CREATE TABLE IF NOT EXISTS {self.users_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                is_superuser TINYINT(1) NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
            """

            create_user_roles = f"""
            CREATE TABLE IF NOT EXISTS {self.user_roles_table} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role_name VARCHAR(100) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user_role (user_id, role_name),
                CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id)
                    REFERENCES {self.users_table}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
            """

            create_user_permissions = f"""
            CREATE TABLE IF NOT EXISTS {self.user_permissions_table} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                permission_name VARCHAR(150) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user_permission (user_id, permission_name),
                CONSTRAINT fk_user_permissions_user FOREIGN KEY (user_id)
                    REFERENCES {self.users_table}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET={charset}
            """

            await MySQLDataAccess.execute_query(create_users, fetch_all=False)
            await MySQLDataAccess.execute_query(create_user_roles, fetch_all=False)
            await MySQLDataAccess.execute_query(create_user_permissions, fetch_all=False)

            self.__class__._initialized = True
            logger.info("✅ 用户相关MySQL数据表已准备就绪")

    async def create_user(self, user_create: UserCreate) -> User:
        """创建新用户"""

        await self._ensure_tables()

        if await self.get_user_by_username(user_create.username):
            raise ValueError("用户名已存在")

        if await self.get_user_by_email(user_create.email):
            raise ValueError("邮箱已存在")

        hashed_password = get_password_hash(user_create.password)

        data = {
            "username": user_create.username,
            "email": user_create.email,
            "hashed_password": hashed_password,
            "full_name": user_create.full_name,
            "is_active": 1,
            "is_superuser": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        user_id = await MySQLDataAccess.insert_data(self.users_table, data, return_id=True)
        logger.info("👤 创建用户成功: %s", user_create.username)
        return await self.get_user_by_id(str(user_id))

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户信息"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        row = await MySQLDataAccess.execute_query(
            f"SELECT * FROM {self.users_table} WHERE id = :user_id",
            {"user_id": user_id_int},
            fetch_one=True,
            fetch_all=False,
        )

        if not row:
            return None

        return await self._hydrate_user(row)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户信息"""

        await self._ensure_tables()

        row = await MySQLDataAccess.execute_query(
            f"SELECT * FROM {self.users_table} WHERE username = :username",
            {"username": username},
            fetch_one=True,
            fetch_all=False,
        )

        if not row:
            return None

        return await self._hydrate_user(row)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户信息"""

        await self._ensure_tables()

        row = await MySQLDataAccess.execute_query(
            f"SELECT * FROM {self.users_table} WHERE email = :email",
            {"email": email},
            fetch_one=True,
            fetch_all=False,
        )

        if not row:
            return None

        return await self._hydrate_user(row)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户名和密码"""

        user = await self.get_user_by_username(username)
        if not user or not user.hashed_password:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """更新用户信息"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        update_data = user_update.dict(exclude_unset=True)

        if "username" in update_data:
            existing = await self.get_user_by_username(update_data["username"])
            if existing and existing.id != user_id_int:
                raise ValueError("用户名已存在")

        if "email" in update_data:
            existing = await self.get_user_by_email(update_data["email"])
            if existing and existing.id != user_id_int:
                raise ValueError("邮箱已存在")

        if not update_data:
            return await self.get_user_by_id(str(user_id_int))

        update_data["updated_at"] = datetime.now()

        set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys()])

        params = {**update_data, "user_id": user_id_int}

        await MySQLDataAccess.execute_query(
            f"UPDATE {self.users_table} SET {set_clause} WHERE id = :user_id",
            params,
            fetch_all=False,
        )

        return await self.get_user_by_id(str(user_id_int))

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return False

        affected = await MySQLDataAccess.delete_data(
            self.users_table,
            "id = :user_id",
            {"user_id": user_id_int},
        )

        return affected > 0

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""

        await self._ensure_tables()

        rows = await MySQLDataAccess.execute_query(
            f"SELECT * FROM {self.users_table} ORDER BY id LIMIT :limit OFFSET :skip",
            {"limit": limit, "skip": skip},
            fetch_all=True,
        )

        users: List[User] = []
        for row in rows or []:
            users.append(await self._hydrate_user(row))
        return users

    async def add_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        """为用户添加角色"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        for role in roles:
            role_name = role.strip()
            if not role_name:
                continue

            await MySQLDataAccess.execute_query(
                f"""
                INSERT INTO {self.user_roles_table} (user_id, role_name, created_at, updated_at)
                VALUES (:user_id, :role_name, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    updated_at = VALUES(updated_at)
                """,
                {"user_id": user_id_int, "role_name": role_name},
                fetch_all=False,
            )

        return await self.get_user_by_id(str(user_id_int))

    async def remove_roles(self, user_id: str, roles: List[str]) -> Optional[User]:
        """移除用户角色"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        for role in roles:
            role_name = role.strip()
            if not role_name:
                continue

            await MySQLDataAccess.execute_query(
                f"DELETE FROM {self.user_roles_table} WHERE user_id = :user_id AND role_name = :role_name",
                {"user_id": user_id_int, "role_name": role_name},
                fetch_all=False,
            )

        return await self.get_user_by_id(str(user_id_int))

    async def add_permissions(self, user_id: str, permissions: List[str]) -> Optional[User]:
        """为用户添加权限"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        for permission in permissions:
            permission_name = permission.strip()
            if not permission_name:
                continue

            await MySQLDataAccess.execute_query(
                f"""
                INSERT INTO {self.user_permissions_table} (user_id, permission_name, created_at, updated_at)
                VALUES (:user_id, :permission_name, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    updated_at = VALUES(updated_at)
                """,
                {"user_id": user_id_int, "permission_name": permission_name},
                fetch_all=False,
            )

        return await self.get_user_by_id(str(user_id_int))

    async def remove_permissions(self, user_id: str, permissions: List[str]) -> Optional[User]:
        """移除用户权限"""

        await self._ensure_tables()

        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None

        for permission in permissions:
            permission_name = permission.strip()
            if not permission_name:
                continue

            await MySQLDataAccess.execute_query(
                f"DELETE FROM {self.user_permissions_table} WHERE user_id = :user_id AND permission_name = :permission_name",
                {"user_id": user_id_int, "permission_name": permission_name},
                fetch_all=False,
            )

        return await self.get_user_by_id(str(user_id_int))

    async def create_superuser(
        self, username: str, email: str, password: str, full_name: Optional[str] = None
    ) -> User:
        """创建超级用户"""

        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
        )

        user = await self.create_user(user_create)
        await self.update_user(str(user.id), UserUpdate(is_superuser=True))
        return await self.get_user_by_id(str(user.id))

    async def _hydrate_user(self, row: Dict[str, Any]) -> User:
        """构造包含角色和权限信息的用户模型"""

        normalized = self._normalize_user_row(row)
        user_id = normalized["id"]
        normalized["roles"] = await self._fetch_roles(user_id)
        normalized["permissions"] = await self._fetch_permissions(user_id)
        return User(**normalized)

    async def _fetch_roles(self, user_id: int) -> List[str]:
        rows = await MySQLDataAccess.execute_query(
            f"SELECT role_name FROM {self.user_roles_table} WHERE user_id = :user_id",
            {"user_id": user_id},
            fetch_all=True,
        )
        return [row["role_name"] for row in (rows or [])]

    async def _fetch_permissions(self, user_id: int) -> List[str]:
        rows = await MySQLDataAccess.execute_query(
            f"SELECT permission_name FROM {self.user_permissions_table} WHERE user_id = :user_id",
            {"user_id": user_id},
            fetch_all=True,
        )
        return [row["permission_name"] for row in (rows or [])]

    def _normalize_user_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(row)
        data["is_active"] = bool(data.get("is_active", True))
        data["is_superuser"] = bool(data.get("is_superuser", False))
        data["created_at"] = self._ensure_datetime(data.get("created_at"))
        data["updated_at"] = self._ensure_datetime(data.get("updated_at"))
        return data

    @staticmethod
    def _ensure_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()
