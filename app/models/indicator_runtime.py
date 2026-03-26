from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator


SupportedIndicatorName = Literal["sma", "ema", "rsi", "macd"]


class IndicatorDefinition(BaseModel):
    name: SupportedIndicatorName = Field(..., description="Indicator name")
    params: Dict[str, float] = Field(default_factory=dict, description="Indicator parameters")


class IndicatorComputeRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol, e.g. SH600519")
    frequency: Literal["d", "w", "m", "5"] = Field("d", description="K-line frequency")
    indicators: List[IndicatorDefinition] = Field(..., description="Indicators to calculate")
    source_field: str = Field("close", description="Source field used by indicators")
    lookback: int = Field(200, ge=30, le=2000, description="How many bars to read from MongoDB")
    persist: bool = Field(False, description="Persist computed indicators into indicator_data")
    target: str = Field("primary", description="MongoDB target alias")

    @validator("symbol")
    def normalize_symbol(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("symbol is required")
        return normalized

    @validator("source_field")
    def normalize_source_field(cls, value: str) -> str:
        normalized = (value or "").strip().lower()
        if normalized not in {"open", "high", "low", "close"}:
            raise ValueError("source_field must be one of open/high/low/close")
        return normalized

    @validator("indicators")
    def validate_indicators(cls, value: List[IndicatorDefinition]) -> List[IndicatorDefinition]:
        if not value:
            raise ValueError("at least one indicator is required")
        return value


class IndicatorSeriesPoint(BaseModel):
    timestamp: datetime
    values: Dict[str, float] = Field(default_factory=dict)


class IndicatorComputeResult(BaseModel):
    symbol: str
    frequency: str
    indicator: str
    points: List[IndicatorSeriesPoint] = Field(default_factory=list)


class IndicatorComputeResponse(BaseModel):
    symbol: str
    frequency: str
    source_field: str
    lookback: int
    results: List[IndicatorComputeResult] = Field(default_factory=list)
    persisted_records: int = 0
