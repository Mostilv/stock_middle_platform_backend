from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class IndicatorRecord(BaseModel):
    """单条指标数据记录，由外部计算服务推送"""

    symbol: str = Field(..., description="股票代码，例如 SH600519")
    indicator: str = Field(..., description="指标唯一标识，例如 RSI14")
    timeframe: str = Field(
        "1d", description="指标对应的时间粒度，默认使用日线（1d）"
    )
    timestamp: datetime = Field(..., description="指标生成时间，自动转换为 UTC")
    value: Optional[float] = Field(None, description="指标主数值，可选")
    values: Dict[str, float] = Field(
        default_factory=dict, description="指标附加数值集合，例如 MACD fast/slow"
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="指标额外结构化数据，保持原样存储"
    )
    tags: List[str] = Field(default_factory=list, description="可选的标签，用于筛选")

    @validator("symbol")
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("股票代码不能为空")
        return normalized

    @validator("indicator")
    def normalize_indicator(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("指标标识不能为空")
        return normalized.lower()

    @validator("timeframe")
    def normalize_timeframe(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("时间粒度不能为空")
        return normalized.lower()

    @validator("tags", each_item=True)
    def normalize_tag(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("标签内容不能为空")
        return normalized

    @root_validator
    def ensure_value_payload(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        has_value = values.get("value") is not None
        has_values = bool(values.get("values"))
        has_payload = bool(values.get("payload"))
        if not any([has_value, has_values, has_payload]):
            raise ValueError("至少提供 value、values 或 payload 其中一项")
        return values

    @staticmethod
    def normalize_timestamp(value: datetime) -> datetime:
        if value.tzinfo:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class IndicatorPushRequest(BaseModel):
    """批量推送指标请求"""

    provider: str = Field(
        "external", description="推送来源标识，用于追踪数据渠道"
    )
    records: List[IndicatorRecord] = Field(..., description="指标记录列表")

    @validator("provider")
    def normalize_provider(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("provider 不能为空")
        return normalized.lower()

    @validator("records")
    def ensure_records(cls, value: List[IndicatorRecord]) -> List[IndicatorRecord]:
        if not value:
            raise ValueError("records 不可为空")
        return value


class IndicatorWriteSummary(BaseModel):
    """指标写入结果统计"""

    total: int = Field(..., ge=0, description="本次推送的总记录数")
    matched: int = Field(..., ge=0, description="命中但数据未变化的记录数")
    modified: int = Field(..., ge=0, description="更新成功的记录数")
    upserted: int = Field(..., ge=0, description="新插入的记录数")


class IndicatorQueryItem(IndicatorRecord):
    """面向查询结果的指标记录"""

    id: str = Field(..., description="MongoDB 文档 ID")
    provider: str = Field(..., description="记录来源标识")
    ingested_at: datetime = Field(..., description="写入时间，UTC")


class IndicatorQueryResponse(BaseModel):
    """指标查询响应"""

    total: int = Field(..., ge=0, description="符合条件的记录总数")
    data: List[IndicatorQueryItem] = Field(
        default_factory=list, description="指标记录列表"
    )
