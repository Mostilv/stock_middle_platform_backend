from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from .models import Position

_POSITIONS: List[Position] = []
_POSITION_ID = 1


async def save_positions(session, positions: Iterable[dict]) -> None:  # session kept for compatibility
    global _POSITION_ID
    for payload in positions:
        position = Position(
            id=_POSITION_ID,
            as_of=payload.get("as_of", datetime.utcnow()),
            code=payload["code"],
            qty=float(payload.get("qty", 0.0)),
            weight=float(payload.get("weight", 0.0)),
            avg_cost=float(payload.get("avg_cost", 0.0)),
            market_value=float(payload.get("market_value", 0.0)),
            source=payload.get("source", "joinquant"),
        )
        _POSITIONS.append(position)
        _POSITION_ID += 1


async def get_latest_as_of(session) -> Optional[datetime]:
    if not _POSITIONS:
        return None
    return max(p.as_of for p in _POSITIONS)


async def get_current_positions(session) -> List[Position]:
    latest = await get_latest_as_of(session)
    if latest is None:
        return []
    return [p for p in _POSITIONS if p.as_of == latest]


async def list_history(session, code: Optional[str] = None, limit: int = 100) -> List[Position]:
    records = [p for p in _POSITIONS if code is None or p.code == code]
    records.sort(key=lambda p: p.as_of, reverse=True)
    return records[:limit]


__all__ = ["save_positions", "get_current_positions", "list_history", "get_latest_as_of"]
