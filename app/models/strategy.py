from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

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
    source: str = Field("internal", description="策略来源，例如joinquant")
    external_id: Optional[str] = Field(None, description="外部平台的策略标识")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    last_signal_at: Optional[datetime] = Field(None, description="最近一次调仓信号时间")
    last_positions_at: Optional[datetime] = Field(None, description="最近一次持仓同步时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        orm_mode = True


# 策略创建模型
class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    strategy_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field("internal", description="策略来源")
    external_id: Optional[str] = Field(None, description="外部平台策略标识")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# 策略更新模型
class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    strategy_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# 策略响应模型
class Strategy(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    user_id: int
    is_public: bool
    is_active: bool
    strategy_type: str
    parameters: Dict[str, Any]
    source: str
    external_id: Optional[str] = None
    metadata: Dict[str, Any]
    last_signal_at: Optional[datetime] = None
    last_positions_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 策略订阅模型
class StrategySubscription(BaseModel):
    id: Optional[int] = Field(default=None, description="订阅ID")
    user_id: int = Field(..., description="用户ID")
    strategy_id: str = Field(..., description="策略ID")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        orm_mode = True


# 策略订阅创建模型
class StrategySubscriptionCreate(BaseModel):
    strategy_id: str


class StrategySubscriptionAdminCreate(BaseModel):
    strategy_id: str
    user_id: int


class StrategySubscriptionUpdate(BaseModel):
    is_active: Optional[bool] = None


# 策略订阅响应模型
class StrategySubscriptionResponse(BaseModel):
    id: str
    user_id: int
    strategy_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    strategy: Optional[Strategy] = None

    class Config:
        orm_mode = True


class StrategySignal(BaseModel):
    id: str
    strategy_id: str
    external_strategy_id: Optional[str] = None
    code: str
    side: Literal["BUY", "SELL", "HOLD", "CLOSE", "UNKNOWN"] = "UNKNOWN"
    quantity: float = 0.0
    price: float = 0.0
    signal_type: str = "rebalance"
    triggered_at: datetime
    batch_id: Optional[str] = None
    source: str = "joinquant"
    note: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class StrategyPosition(BaseModel):
    id: str
    strategy_id: str
    external_strategy_id: Optional[str] = None
    code: str
    quantity: float = 0.0
    weight: Optional[float] = None
    price: Optional[float] = None
    market_value: Optional[float] = None
    as_of: datetime
    batch_id: Optional[str] = None
    source: str = "joinquant"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
