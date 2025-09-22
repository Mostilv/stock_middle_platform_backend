from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .deps import get_db_session, get_rebalance_service, require_api_key
from ..repo.mysql import signals_repo
from ..service.rebalance_service import RebalanceService

router = APIRouter(prefix="/signals", tags=["signals"], dependencies=[Depends(require_api_key)])
rebalance_router = APIRouter(prefix="/rebalance", tags=["rebalance"], dependencies=[Depends(require_api_key)])


@router.get("/recent", summary="Recent trading signals")
async def list_recent_signals(
    limit: int = Query(default=50, le=200),
    session=Depends(get_db_session),
) -> dict:
    signals = await signals_repo.list_recent(session, limit=limit)
    return {
        "items": [
            {
                "code": s.code,
                "side": s.side,
                "qty": s.qty,
                "price": s.price,
                "reason": s.reason,
                "source": s.source,
                "ts": s.ts.isoformat(timespec="seconds"),
            }
            for s in signals
        ]
    }


@rebalance_router.get("/plans", summary="List rebalance plans")
async def list_rebalance_plans(
    limit: int = Query(default=20, le=100),
    session=Depends(get_db_session),
    service: RebalanceService = Depends(get_rebalance_service),
) -> dict:
    return await service.list_plans(session, limit)


@rebalance_router.get("/{plan_id}", summary="Get rebalance plan detail")
async def get_rebalance_plan(
    plan_id: int,
    session=Depends(get_db_session),
    service: RebalanceService = Depends(get_rebalance_service),
) -> dict:
    try:
        return await service.get_plan(session, plan_id)
    except ValueError as exc:  # noqa: F841
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found") from exc


@rebalance_router.post("/confirm", summary="Confirm execution of plan")
async def confirm_plan(
    payload: Dict[str, Any],
    session=Depends(get_db_session),
    service: RebalanceService = Depends(get_rebalance_service),
) -> dict:
    plan_id = int(payload.get("plan_id"))
    notes = payload.get("notes")
    try:
        return await service.confirm_plan(session, plan_id, notes)
    except ValueError as exc:  # noqa: F841
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="plan not found") from exc


__all__ = ["router", "rebalance_router"]
