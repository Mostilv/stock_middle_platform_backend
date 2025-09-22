from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from .models import Signal

_SIGNALS: List[Signal] = []
_SIGNAL_ID = 1


async def insert_signals(session, signals: Iterable[dict]) -> None:
    global _SIGNAL_ID
    for payload in signals:
        record = Signal(
            id=_SIGNAL_ID,
            code=payload["code"],
            side=payload.get("side", "BUY"),
            qty=float(payload.get("qty", 0.0)),
            price=float(payload.get("price", 0.0)),
            reason=payload.get("reason", ""),
            source=payload.get("source", "joinquant"),
            ts=payload.get("ts", datetime.utcnow()),
            meta=payload.get("meta", {}),
        )
        _SIGNALS.append(record)
        _SIGNAL_ID += 1


async def list_recent(session, limit: int = 50) -> List[Signal]:
    return sorted(_SIGNALS, key=lambda s: s.ts, reverse=True)[:limit]


__all__ = ["insert_signals", "list_recent"]
