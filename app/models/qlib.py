import datetime as dt
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, root_validator, validator

_RESERVED_EXTRA_FIELDS = {
    "instrument",
    "datetime",
    "freq",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "factor",
    "vwap",
    "turnover",
    "limit_status",
    "suspended",
    "provider",
    "market",
    "created_at",
    "updated_at",
}


class QlibStockRecord(BaseModel):
    instrument: str = Field(..., description="Qlib instrument code, e.g. SH600519.")
    datetime: dt.datetime = Field(
        ..., description="Bar timestamp; tz-aware datetimes are converted into UTC."
    )
    freq: Literal["1d", "1m", "5m", "15m", "30m", "60m"] = Field(
        "1d", description="Qlib frequency token."
    )
    open: float = Field(..., description="Open price.")
    high: float = Field(..., description="High price.")
    low: float = Field(..., description="Low price.")
    close: float = Field(..., description="Close price.")
    volume: float = Field(..., ge=0, description="Turnover volume.")
    amount: Optional[float] = Field(
        None, ge=0, description="Transaction amount (aka money)."
    )
    factor: Optional[float] = Field(
        None, ge=0, description="Adjustment factor matching qlib raw data."
    )
    vwap: Optional[float] = Field(
        None, ge=0, description="Volume weighted average price."
    )
    turnover: Optional[float] = Field(None, ge=0, description="Turnover ratio.")
    limit_status: Optional[Literal["limit_up", "limit_down", "none"]] = Field(
        None, description="Limit status flag from qlib feeds."
    )
    suspended: bool = Field(
        False, description="Whether the instrument is suspended on this bar."
    )
    extra_fields: Dict[str, float] = Field(
        default_factory=dict,
        description="Additional qlib factor columns (e.g., Ref($close,1)).",
    )

    @validator("instrument")
    def normalize_instrument(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("instrument code cannot be blank")
        return normalized.upper()

    @root_validator
    def ensure_price_bounds(cls, values: Dict[str, float]) -> Dict[str, float]:
        high = values.get("high")
        low = values.get("low")
        if high is not None and low is not None and high < low:
            raise ValueError("high cannot be lower than low")
        return values

    @validator("extra_fields")
    def ensure_valid_extra_fields(cls, value: Dict[str, float]) -> Dict[str, float]:
        reserved = _RESERVED_EXTRA_FIELDS
        duplicates = set(value).intersection(reserved)
        if duplicates:
            reserved_list = ", ".join(sorted(duplicates))
            raise ValueError(f"extra_fields overlaps with reserved columns: {reserved_list}")
        return value

    @staticmethod
    def normalize_datetime(value: dt.datetime) -> dt.datetime:
        if value.tzinfo:
            return value.astimezone(dt.timezone.utc).replace(tzinfo=None)
        return value


class QlibStockBatch(BaseModel):
    provider: str = Field(
        "external",
        description="Data provider label recorded next to the ingested qlib rows.",
    )
    market: str = Field(
        "cn",
        description="Market alias compatible with qlib data directories (e.g. cn/us).",
    )
    timezone: str = Field(
        "Asia/Shanghai",
        description="IANA timezone string describing the source timestamps.",
    )
    records: List[QlibStockRecord] = Field(
        ..., description="List of qlib-formatted stock bars."
    )

    @validator("records")
    def ensure_records_non_empty(cls, value: List[QlibStockRecord]) -> List[QlibStockRecord]:
        if not value:
            raise ValueError("records payload cannot be empty")
        return value


class QlibIngestSummary(BaseModel):
    total: int = Field(..., ge=0, description="Total number of rows processed.")
    matched: int = Field(..., ge=0, description="Existing bars matched in the database.")
    modified: int = Field(..., ge=0, description="Existing bars that changed.")
    upserted: int = Field(..., ge=0, description="New bars inserted during ingest.")
