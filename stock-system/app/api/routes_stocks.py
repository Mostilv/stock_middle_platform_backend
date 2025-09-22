from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query

from .deps import get_data_service, get_indicator_service, require_api_key
from ..service.data_refresh_service import DataRefreshService
from ..service.indicator_service import IndicatorService

router = APIRouter(prefix="/stocks", tags=["stocks"], dependencies=[Depends(require_api_key)])


@router.get("/search", summary="Search stocks")
async def search_stocks(
    q: Optional[str] = Query(default=None, description="Query string"),
    market: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    cursor: Optional[str] = Query(default=None),
    service: DataRefreshService = Depends(get_data_service),
) -> dict:
    items = await service.search_stocks(q)
    return {"items": items[:limit], "next_cursor": None}


@router.get("/{code}/profile", summary="Stock profile")
async def get_profile(
    code: str = Path(..., description="Stock code"),
    service: DataRefreshService = Depends(get_data_service),
) -> dict:
    return await service.get_profile(code)


@router.get("/{code}/kline", summary="K line data")
async def get_kline(
    code: str,
    period: str = Query(default="daily"),
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    adjust: str = Query(default="qfq"),
    limit: int = Query(default=200, le=1000),
    cursor: Optional[str] = Query(default=None),
    service: DataRefreshService = Depends(get_data_service),
) -> dict:
    bars = await service.get_kline(code, period, start, end, adjust, limit)
    return {
        "code": code,
        "period": period,
        "adjust": adjust,
        "bars": bars,
        "next_cursor": None,
    }


@router.get("/{code}/technicals", summary="Technical indicators")
async def get_technicals(
    code: str,
    names: str = Query(..., description="Comma separated indicator names"),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    limit: int = Query(default=200, le=1000),
    indicator_service: IndicatorService = Depends(get_indicator_service),
) -> dict:
    indicators: List[str] = [name.strip() for name in names.split(",") if name.strip()]
    items = []
    for name in indicators:
        data = await indicator_service.query_indicator(code, name, start, end, limit)
        items.append({"name": name, "params": {}, "series": data["series"]})
    return {"code": code, "indicators": items, "next_cursor": None}
