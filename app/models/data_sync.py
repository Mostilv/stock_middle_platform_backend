from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MarketIndicesPushRequest(BaseModel):
    target: str = Field(default="primary", description="Target database alias")
    data: Dict[str, Any] = Field(..., description="Map of index symbol to index data object")

class LimitUpRecord(BaseModel):
    code: str
    name: str
    price: Optional[float] = None
    changePercent: Optional[float] = None
    amount: Optional[float] = None
    marketCap: Optional[float] = None
    totalMarketCap: Optional[float] = None
    turnoverRate: Optional[float] = None
    limitUpDays: Optional[int] = 1
    firstLimitUpTime: Optional[str] = None
    lastLimitUpTime: Optional[str] = None
    limitUpFund: Optional[float] = None
    industry: Optional[str] = None
    date: str

class LimitUpPoolPushRequest(BaseModel):
    target: str = Field(default="primary", description="Target database alias")
    date: str = Field(..., description="Date string YYYYMMDD or YYYY-MM-DD")
    data: List[LimitUpRecord] = Field(..., description="List of limit up pool records")

class DataPushResponse(BaseModel):
    ok: bool = True
    message: str = "Success"
    records_saved: int = 0
