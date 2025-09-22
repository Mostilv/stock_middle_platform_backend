from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Signal:
    id: int
    code: str
    side: str
    qty: float
    price: float
    reason: str
    source: str
    ts: datetime
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    id: int
    as_of: datetime
    code: str
    qty: float
    weight: float
    avg_cost: float
    market_value: float
    source: str


@dataclass
class JobLog:
    id: int
    job_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    ok: bool = True
    error: Optional[str] = None


@dataclass
class MailLog:
    id: int
    sent_at: datetime
    subject: str
    recipients: List[str]
    ok: bool
    error: Optional[str]


@dataclass
class IndicatorDef:
    id: int
    name: str
    description: str
    params_schema: Dict[str, Any]
    impl_ref: str
    created_at: datetime
    updated_at: datetime


@dataclass
class RebalancePlan:
    plan_id: int
    date: datetime
    targets: Dict[str, Any]
    estimation: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime


__all__ = [
    "Signal",
    "Position",
    "JobLog",
    "MailLog",
    "IndicatorDef",
    "RebalancePlan",
]
