from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    is_active: bool = True
    strategy_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    strategy_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Strategy(StrategyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class StrategySubscription(BaseModel):
    id: str
    user_id: str
    strategy_id: str
    is_active: bool = True
    created_at: datetime


class StrategySubscriptionCreate(BaseModel):
    strategy_id: str


class StrategySubscriptionResponse(BaseModel):
    id: str
    user_id: str
    strategy_id: str
    is_active: bool
    created_at: datetime
    strategy: Optional[Strategy] = None
