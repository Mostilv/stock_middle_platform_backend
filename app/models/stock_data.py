from datetime import date, datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator


def _normalize_symbol(value: str) -> str:
    normalized = (value or "").strip().upper().replace(".", "")
    if not normalized:
        raise ValueError("symbol 不能为空")
    if len(normalized) < 5:
        raise ValueError("symbol 长度异常")
    return normalized


def _parse_compact_date(value: Any) -> Any:
    if isinstance(value, str) and len(value) == 8 and value.isdigit():
        return datetime.strptime(value, "%Y%m%d").date()
    return value


class DataSinkTargetInfo(BaseModel):
    dataset: str
    target: str
    database: str
    collection: str
    description: str = ""


class DataPushConfigResponse(BaseModel):
    datasets: Dict[str, List[DataSinkTargetInfo]]
    schemas: Dict[str, Dict[str, Any]]


class DataWriteSummary(BaseModel):
    total: int = Field(..., ge=0)
    matched: int = Field(..., ge=0)
    modified: int = Field(..., ge=0)
    upserted: int = Field(..., ge=0)


class StockBasicRecord(BaseModel):
    symbol: str = Field(..., description="标准化股票代码，例如 SH600519")
    name: str = Field(..., description="证券简称")
    exchange: str = Field(..., description="交易所代码，如 SH/SZ/BJ")
    list_date: Optional[date] = Field(
        None, description="上市日期，YYYY-MM-DD"
    )
    delist_date: Optional[date] = Field(
        None, description="退市日期，YYYY-MM-DD"
    )
    status: Optional[str] = Field(
        None, description="上市状态，如 active/delisted"
    )
    type: Optional[str] = Field(None, description="证券类别，如 stock/index")
    market: Optional[str] = Field(None, description="市场板块描述")
    industry: Optional[str] = Field(None, description="行业名称")
    area: Optional[str] = Field(None, description="地区")
    currency: Optional[str] = Field(None, description="交易货币")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="原始字段快照"
    )

    @validator("symbol", pre=True)
    def ensure_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)

    @validator("exchange", pre=True)
    def normalize_exchange(cls, value: str, values: Dict[str, Any]) -> str:
        exchange = (value or "").strip().upper()
        if not exchange and "symbol" in values:
            exchange = values["symbol"][:2]
        if not exchange:
            raise ValueError("exchange 不能为空")
        return exchange

    @validator("list_date", "delist_date", pre=True)
    def normalize_dates(cls, value: Any) -> Any:
        return _parse_compact_date(value)

    @validator("status", "type", "market", "industry", "area", "currency", pre=True)
    def strip_strings(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = str(value).strip()
        return cleaned or None


class StockBasicBatch(BaseModel):
    target: str = Field(
        "primary", description="数据写入目标别名，来源于 /stocks/targets 接口"
    )
    provider: str = Field("astock", description="数据来源标识")
    items: List[StockBasicRecord] = Field(..., description="股票基础信息列表")

    @validator("target", "provider")
    def normalize_token(cls, value: str) -> str:
        cleaned = (value or "").strip().lower()
        if not cleaned:
            raise ValueError("target/provider 不能为空")
        return cleaned

    @validator("items")
    def ensure_items(cls, value: List[StockBasicRecord]) -> List[StockBasicRecord]:
        if not value:
            raise ValueError("items 不能为空")
        return value


class StockKlineRecord(BaseModel):
    symbol: str = Field(..., description="标准化股票代码，例如 SH600519")
    frequency: Literal["d", "w", "m", "15", "30", "60"] = Field(
        ..., description="K 线周期标识"
    )
    timestamp: datetime = Field(..., description="K 线时间戳（UTC）")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., ge=0, description="成交量")
    amount: Optional[float] = Field(None, ge=0, description="成交额")
    turnover_rate: Optional[float] = Field(None, description="换手率，单位 %")
    adjust_flag: Optional[str] = Field(None, description="复权标识")
    trade_status: Optional[Literal["trading", "halted"]] = Field(
        None, description="交易状态"
    )
    pct_change: Optional[float] = Field(None, description="涨跌幅，单位 %")
    pe_ttm: Optional[float] = Field(None, description="市盈率 TTM")
    pb_mrq: Optional[float] = Field(None, description="市净率 MRQ")
    ps_ttm: Optional[float] = Field(None, description="市销率 TTM")
    pcf_ncf_ttm: Optional[float] = Field(None, description="市现率 TTM")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="原始字段快照"
    )

    @validator("symbol", pre=True)
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(value)

    @validator("timestamp", pre=True)
    def normalize_timestamp(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                normalized = value.replace("Z", "+00:00")
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                raise ValueError("timestamp 必须为 ISO8601 格式")
            if parsed.tzinfo:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        if isinstance(value, datetime) and value.tzinfo:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @validator("frequency", pre=True)
    def normalize_frequency(cls, value: Any) -> str:
        return str(value).strip().lower()

    @validator("trade_status", pre=True)
    def normalize_status(cls, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        if isinstance(value, bool):
            return "trading" if value else "halted"
        text = str(value).strip().lower()
        if text in {"1", "true", "trading", "open"}:
            return "trading"
        if text in {"0", "false", "halted", "suspend"}:
            return "halted"
        raise ValueError("trade_status 仅支持 trading/halted")


class StockKlineBatch(BaseModel):
    target: str = Field("primary", description="数据写入目标别名")
    provider: str = Field("astock", description="数据来源标识")
    items: List[StockKlineRecord] = Field(..., description="K 线记录列表")

    @validator("target", "provider")
    def normalize_token(cls, value: str) -> str:
        cleaned = (value or "").strip().lower()
        if not cleaned:
            raise ValueError("target/provider 不能为空")
        return cleaned

    @validator("items")
    def ensure_items(cls, value: List[StockKlineRecord]) -> List[StockKlineRecord]:
        if not value:
            raise ValueError("items 不能为空")
        return value
