from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.stock_data import _normalize_symbol


class IntegrityCheckItem(BaseModel):
    symbol: str
    frequency: str = Field(..., description="d, w, m, 5, 15, 30, 60")
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    class Config:
        schema_extra = {
            "example": {
                "symbol": "sh.600000",
                "frequency": "d",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
            }
        }


class IntegrityCheckRequest(BaseModel):
    target: str = Field("primary", description="Database target alias")
    items: List[IntegrityCheckItem]


class IntegrityCheckResult(BaseModel):
    symbol: str
    frequency: str
    count: int
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    status: str = "ok"  # ok, error


class IntegrityCheckResponse(BaseModel):
    results: List[IntegrityCheckResult]
