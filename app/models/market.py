from typing import Dict, List

from pydantic import BaseModel


class MarketSeries(BaseModel):
    current: float
    change: float
    history: List[float]


class MarketDataResponse(BaseModel):
    __root__: Dict[str, MarketSeries]

    def dict(self, *args, **kwargs):  # type: ignore[override]
        return super().dict(*args, **kwargs)["__root__"]
