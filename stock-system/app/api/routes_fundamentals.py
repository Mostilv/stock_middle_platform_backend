from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from .deps import get_fundamentals_service, require_api_key
from ..service.fundamentals_service import FundamentalsService

router = APIRouter(prefix="/fundamentals", tags=["fundamentals"], dependencies=[Depends(require_api_key)])


@router.get("/{code}", summary="Fundamental snapshot")
async def get_fundamental_snapshot(
    code: str = Path(...),
    period: str = Query(default="ttm"),
    fields: str | None = Query(default=None),
    service: FundamentalsService = Depends(get_fundamentals_service),
) -> dict:
    snapshot = await service.get_snapshot(code, period)
    if fields:
        requested = {field: snapshot["metrics"].get(field) for field in fields.split(",")}
        snapshot["metrics"] = requested
    return snapshot


@router.get("/{code}/timeline", summary="Fundamental timeline")
async def get_fundamental_timeline(
    code: str,
    limit: int = Query(default=8, le=20),
    service: FundamentalsService = Depends(get_fundamentals_service),
) -> dict:
    return await service.get_timeline(code, limit)
