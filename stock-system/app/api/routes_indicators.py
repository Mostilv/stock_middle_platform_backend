from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from .deps import get_db_session, get_indicator_service, require_api_key
from ..service.indicator_service import IndicatorService

router = APIRouter(prefix="/indicators", tags=["indicators"], dependencies=[Depends(require_api_key)])


@router.post("/custom/define", summary="Define custom indicator")
async def define_custom_indicator(
    payload: Dict[str, Any],
    indicator_service: IndicatorService = Depends(get_indicator_service),
    session=Depends(get_db_session),
) -> dict:
    record = await indicator_service.define_custom_indicator(
        session,
        payload["name"],
        payload.get("description", ""),
        payload.get("params_schema", {}),
        payload.get("impl_ref", ""),
    )
    return record


@router.post("/custom/compute", summary="Compute custom indicator")
async def compute_custom_indicator(
    payload: Dict[str, Any],
    indicator_service: IndicatorService = Depends(get_indicator_service),
    session=Depends(get_db_session),
) -> dict:
    summary = await indicator_service.compute_custom_indicator(
        session,
        payload.get("codes", []),
        payload.get("indicator"),
        payload.get("params", {}),
        payload.get("start"),
        payload.get("end"),
    )
    summary["async"] = payload.get("async", False)
    return summary


@router.get("/custom/query", summary="Query custom indicator")
async def query_custom_indicator(
    code: str = Query(...),
    indicator: str = Query(...),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=1000),
    indicator_service: IndicatorService = Depends(get_indicator_service),
) -> dict:
    return await indicator_service.query_indicator(code, indicator, start, end, limit)
