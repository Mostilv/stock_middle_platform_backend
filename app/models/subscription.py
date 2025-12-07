from typing import List

from pydantic import BaseModel


class SubscriptionStrategy(BaseModel):
    id: str
    name: str
    summary: str
    riskLevel: str
    signalFrequency: str
    lastSignal: str
    performance: float
    subscribed: bool
    channels: List[str]
    tags: List[str]
    subscribers: int


class StrategySubscriptionState(BaseModel):
    strategies: List[SubscriptionStrategy]
    blacklist: List[str]
