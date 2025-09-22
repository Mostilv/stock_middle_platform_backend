from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from .deps import get_db_session, require_api_key
from ..repo.mysql import positions_repo

router = APIRouter(prefix="/positions", tags=["positions"], dependencies=[Depends(require_api_key)])


@router.get("/current", summary="Current aggregated positions")
async def get_current_positions(session=Depends(get_db_session)) -> dict:
    positions = await positions_repo.get_current_positions(session)
    return {
        "items": [
            {
                "code": p.code,
                "qty": p.qty,
                "weight": p.weight,
                "avg_cost": p.avg_cost,
                "market_value": p.market_value,
                "as_of": p.as_of.isoformat(),
                "source": p.source,
            }
            for p in positions
        ]
    }


@router.get("/history", summary="Position history")
async def get_positions_history(
    code: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    session=Depends(get_db_session),
) -> dict:
    history = await positions_repo.list_history(session, code=code, limit=limit)
    return {
        "items": [
            {
                "code": p.code,
                "qty": p.qty,
                "weight": p.weight,
                "avg_cost": p.avg_cost,
                "market_value": p.market_value,
                "as_of": p.as_of.isoformat(),
                "source": p.source,
            }
            for p in history
        ]
    }
