from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import (
    get_db_indicator_service,
    get_indicator_service,
    require_permissions,
)
from app.models.indicator import (
    IndicatorPushRequest,
    IndicatorQueryResponse,
    IndicatorWriteSummary,
)
from app.models.indicator_runtime import (
    IndicatorComputeRequest,
    IndicatorComputeResponse,
)
from app.models.user import User
from app.services.db_indicator_service import DatabaseIndicatorService
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.post(
    "/records",
    response_model=IndicatorWriteSummary,
    status_code=status.HTTP_200_OK,
    summary="Persist indicator records",
)
async def push_indicator_records(
    payload: IndicatorPushRequest,
    _: User = Depends(require_permissions(["indicators:write"])),
    service: IndicatorService = Depends(get_indicator_service),
) -> IndicatorWriteSummary:
    try:
        return await service.ingest(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist indicator records: {exc}",
        ) from exc


@router.get(
    "/records",
    response_model=IndicatorQueryResponse,
    summary="Query persisted indicator records",
)
async def query_indicator_records(
    indicator: str = Query(..., description="Indicator name, e.g. rsi_14"),
    symbol: Optional[str] = Query(None, description="Stock symbol, e.g. SH600519"),
    timeframe: Optional[str] = Query(None, description="K-line frequency"),
    start: Optional[datetime] = Query(None, description="Start time"),
    end: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(100, ge=1, le=500, description="Maximum rows to return"),
    skip: int = Query(0, ge=0, description="Rows to skip"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    target: str = Query("primary", description="MongoDB target alias"),
    _: User = Depends(require_permissions(["indicators:read"])),
    service: IndicatorService = Depends(get_indicator_service),
) -> IndicatorQueryResponse:
    try:
        return await service.query(
            indicator=indicator,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
            skip=skip,
            tags=tags,
            target=target,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query indicator records: {exc}",
        ) from exc


@router.post(
    "/calculate",
    response_model=IndicatorComputeResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate indicators directly from stock_kline data",
)
async def calculate_indicator_records(
    payload: IndicatorComputeRequest,
    _: User = Depends(require_permissions(["indicators:read"])),
    service: DatabaseIndicatorService = Depends(get_db_indicator_service),
) -> IndicatorComputeResponse:
    try:
        return await service.calculate(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate indicators: {exc}",
        ) from exc
