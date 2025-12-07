from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_market_data_service, get_optional_active_user
from app.models.market import MarketDataResponse
from app.models.user import User
from app.services.frontend_state_service import MarketDataService

router = APIRouter(prefix="/market", tags=["行情与行业指标"])


def _parse_symbols(raw: Optional[str]) -> Optional[List[str]]:
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


@router.get("/data", response_model=MarketDataResponse)
async def get_market_data(
    symbols: Optional[str] = Query(
        None,
        description="指数名称标识列表，逗号分隔，如 shanghaiIndex,nasdaqIndex",
    ),
    historyDays: int = Query(5, ge=1, le=60, description="返回最近 N 日历史点位"),
    _: User = Depends(get_optional_active_user),
    service: MarketDataService = Depends(get_market_data_service),
):
    symbol_list = _parse_symbols(symbols)
    return await service.get_market_data(symbol_list, historyDays)
