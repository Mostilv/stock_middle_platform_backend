from typing import Optional, List
from datetime import datetime
from app.database import mongodb
from app.models.user import UserInDB, User, UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from bson import ObjectId


class UserService:
    def __init__(self):
        self.collection = mongodb.db.users

    async def create_user(self, user_create: UserCreate) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing_user = await self.get_user_by_username(user_create.username)
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = await self.get_user_by_email(user_create.email)
        if existing_email:
            raise ValueError("邮箱已存在")
        
        # 创建用户文档
        user_dict = user_create.dict()
        user_dict["hashed_password"] = get_password_hash(user_create.password)
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        # 移除明文密码
        del user_dict["password"]
        
        user_in_db = UserInDB(**user_dict)
        result = await self.collection.insert_one(user_in_db.dict(by_alias=True))
        
        # 获取创建的用户
        created_user = await self.get_user_by_id(str(result.inserted_id))
        return created_user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_doc = await self.collection.find_one({"username": username})
        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_doc = await self.collection.find_one({"email": email})
        if user_doc:
            user_doc["id"] = str(user_doc["_id"])
            return User(**user_doc)
        return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_user_by_id(user_id)
        return None

    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        users = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc["_id"])
            users.append(User(**user_doc))
        return users

    async def create_superuser(self, username: str, email: str, password: str, full_name: str = None) -> User:
        """创建超级用户"""
        user_create = UserCreate(
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        user = await self.create_user(user_create)
        
        # 设置为超级用户
        await self.collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": {"is_superuser": True, "updated_at": datetime.utcnow()}}
        )
        
        return await self.get_user_by_id(user.id)
