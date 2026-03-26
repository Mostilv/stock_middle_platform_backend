from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class StockBasicQueryItem(BaseModel):
    id: str
    symbol: str
    name: str
    exchange: str
    status: Optional[str] = None
    type: Optional[str] = None
    market: Optional[str] = None
    industry: Optional[str] = None
    area: Optional[str] = None
    currency: Optional[str] = None
    provider: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class StockKlineQueryItem(BaseModel):
    id: str
    symbol: str
    frequency: str
    timestamp: datetime
    trade_date: Optional[datetime] = None
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    adjust_flag: Optional[str] = None
    trade_status: Optional[str] = None
    pct_change: Optional[float] = None
    provider: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
