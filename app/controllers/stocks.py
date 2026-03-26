from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import (
    get_raw_stock_data_query_service,
    require_permissions,
)
from app.models.stock_query import StockBasicQueryItem, StockKlineQueryItem
from app.models.user import User
from app.services.raw_data_query_service import RawStockDataQueryService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get(
    "/basic",
    response_model=List[StockBasicQueryItem],
    summary="Query stock basic records",
)
async def list_stock_basics(
    symbol: Optional[str] = Query(default=None),
    industry: Optional[str] = Query(default=None),
    exchange: Optional[str] = Query(default=None),
    target: str = Query(default="primary"),
    limit: int = Query(default=50, ge=1, le=500),
    _: User = Depends(require_permissions(["stocks:read"])),
    service: RawStockDataQueryService = Depends(get_raw_stock_data_query_service),
) -> List[StockBasicQueryItem]:
    records = await service.list_stock_basics(
        target=target,
        symbol=symbol,
        industry=industry,
        exchange=exchange,
        limit=limit,
    )
    return [StockBasicQueryItem(**record) for record in records]


@router.get(
    "/basic/symbols",
    response_model=List[str],
    summary="List available stock symbols from stock_basic",
)
async def list_basic_symbols(
    target: str = Query(default="primary"),
    limit: int = Query(default=200, ge=1, le=2000),
    _: User = Depends(require_permissions(["stocks:read"])),
    service: RawStockDataQueryService = Depends(get_raw_stock_data_query_service),
) -> List[str]:
    return await service.list_basic_symbols(target=target, limit=limit)


@router.get(
    "/kline",
    response_model=List[StockKlineQueryItem],
    summary="Query raw stock kline records",
)
async def list_stock_kline(
    symbol: str = Query(...),
    frequency: str = Query(...),
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    target: str = Query(default="primary"),
    limit: int = Query(default=200, ge=1, le=2000),
    _: User = Depends(require_permissions(["stocks:read"])),
    service: RawStockDataQueryService = Depends(get_raw_stock_data_query_service),
) -> List[StockKlineQueryItem]:
    records = await service.list_stock_kline(
        target=target,
        symbol=symbol,
        frequency=frequency,
        start=start,
        end=end,
        limit=limit,
    )
    return [StockKlineQueryItem(**record) for record in records]


@router.get(
    "/kline/symbols",
    response_model=List[str],
    summary="List available stock symbols from stock_kline",
)
async def list_kline_symbols(
    frequency: Optional[str] = Query(default=None),
    target: str = Query(default="primary"),
    limit: int = Query(default=200, ge=1, le=2000),
    _: User = Depends(require_permissions(["stocks:read"])),
    service: RawStockDataQueryService = Depends(get_raw_stock_data_query_service),
) -> List[str]:
    return await service.list_kline_symbols(
        target=target,
        frequency=frequency,
        limit=limit,
    )
