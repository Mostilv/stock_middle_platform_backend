from typing import List, Optional

from pydantic import BaseModel


class SectorData(BaseModel):
    name: str
    count: int
    value: float


class StockItem(BaseModel):
    name: str
    code: str
    time: str
    price: float
    changePercent: float
    volume1: float
    volume2: float
    ratio1: float
    ratio2: float
    sectors: List[str]
    marketCap: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None


class LadderGroup(BaseModel):
    level: int
    count: int
    stocks: List[StockItem]


class LimitUpOverview(BaseModel):
    date: str
    sectors: List[SectorData]
    ladders: List[LadderGroup]
