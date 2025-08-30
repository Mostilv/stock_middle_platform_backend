from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from app.models.user import PyObjectId


# 策略模型
class StrategyInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., index=True)
    description: Optional[str] = None
    user_id: str = Field(..., index=True)  # 策略创建者ID
    is_public: bool = False  # 是否为公开策略
    is_active: bool = True
    strategy_type: str = Field(..., index=True)  # 策略类型
    parameters: Dict[str, Any] = {}  # 策略参数
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# 策略创建模型
class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    strategy_type: str
    parameters: Dict[str, Any] = {}


# 策略更新模型
class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    strategy_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


# 策略响应模型
class Strategy(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    is_public: bool
    is_active: bool
    strategy_type: str
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 策略订阅模型
class StrategySubscription(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., index=True)
    strategy_id: str = Field(..., index=True)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# 策略订阅创建模型
class StrategySubscriptionCreate(BaseModel):
    strategy_id: str


# 策略订阅响应模型
class StrategySubscriptionResponse(BaseModel):
    id: str
    user_id: str
    strategy_id: str
    is_active: bool
    created_at: datetime
    strategy: Optional[Strategy] = None

    class Config:
        from_attributes = True
