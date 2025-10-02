from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class JoinQuantWebhookPayload(BaseModel):
    """聚宽推送的调仓/持仓信号载荷模型"""

    strategy_id: Optional[str] = Field(
        default=None, description="平台内部的策略ID（字符串形式的ObjectId）"
    )
    strategy_code: Optional[str] = Field(
        default=None, description="聚宽侧的策略唯一标识"
    )
    strategy_name: Optional[str] = Field(default=None, description="策略名称")
    source: str = Field(default="joinquant", description="数据来源标识")
    sent_at: Optional[datetime] = Field(
        default=None, description="信号产生时间"
    )
    batch_id: Optional[str] = Field(
        default=None, description="聚合批次ID，用于区分同一时间的推送"
    )
    note: Optional[str] = Field(default=None, description="全局备注")
    orders: List[Dict[str, Any]] = Field(
        default_factory=list, description="调仓订单明细"
    )
    positions: List[Dict[str, Any]] = Field(
        default_factory=list, description="持仓明细"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="额外的上下文信息"
    )

    @validator("sent_at", pre=True)
    def _parse_datetime(cls, value: Any) -> Optional[datetime]:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (OSError, ValueError):
                return None
        if isinstance(value, str):
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None


__all__ = ["JoinQuantWebhookPayload"]
