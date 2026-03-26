from fastapi import APIRouter, Depends

from app.core.deps import get_stock_data_service, require_permissions
from app.models.integrity import IntegrityCheckRequest, IntegrityCheckResponse
from app.models.user import User
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.post(
    "/check",
    response_model=IntegrityCheckResponse,
    summary="Check stored kline integrity",
    description=(
        "Return count and min/max timestamps for the requested symbol, "
        "frequency and date range."
    ),
)
async def check_data_integrity(
    payload: IntegrityCheckRequest,
    _: User = Depends(require_permissions(["stocks:read"])),
    service: StockDataService = Depends(get_stock_data_service),
) -> IntegrityCheckResponse:
    results = await service.check_integrity(payload)
    return IntegrityCheckResponse(results=results)
