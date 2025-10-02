from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# MySQL用户模型
class UserInDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 用户创建模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


# 用户更新模型
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


# 用户响应模型
class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    hashed_password: Optional[str] = Field(default=None, exclude=True)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# 用户登录模型
class UserLogin(BaseModel):
    username: str
    password: str


# 令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str


# 令牌数据模型
class TokenData(BaseModel):
    username: Optional[str] = None
