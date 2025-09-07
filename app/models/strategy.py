from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# 策略模型
class StrategyInDB(BaseModel):
    id: Optional[int] = Field(default=None, description="策略ID")
    name: str = Field(..., description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    user_id: int = Field(..., description="策略创建者ID")
    is_public: bool = Field(False, description="是否为公开策略")
    is_active: bool = Field(True, description="是否激活")
    strategy_type: str = Field(..., description="策略类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        orm_mode = True


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
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    is_public: bool
    is_active: bool
    strategy_type: str
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 策略订阅模型
class StrategySubscription(BaseModel):
    id: Optional[int] = Field(default=None, description="订阅ID")
    user_id: int = Field(..., description="用户ID")
    strategy_id: int = Field(..., description="策略ID")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        orm_mode = True


# 策略订阅创建模型
class StrategySubscriptionCreate(BaseModel):
    strategy_id: int


# 策略订阅响应模型
class StrategySubscriptionResponse(BaseModel):
    id: int
    user_id: int
    strategy_id: int
    is_active: bool
    created_at: datetime
    strategy: Optional[Strategy] = None

    class Config:
        orm_mode = True
