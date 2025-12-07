from typing import List

from pydantic import BaseModel


class PortfolioItem(BaseModel):
    key: str
    stock: str
    code: str
    currentWeight: float
    targetWeight: float
    action: str
    price: float
    quantity: float
    status: str
    createdAt: str
    marketValue: float


class StrategySummary(BaseModel):
    id: str
    name: str
    description: str
    status: str
    totalValue: float
    totalWeight: float
    items: List[PortfolioItem]
    createdAt: str


class PortfolioOverview(BaseModel):
    strategies: List[StrategySummary]
    todayPnL: float
    totalPnL: float
    todayRebalance: int
    todayPendingRebalance: int
