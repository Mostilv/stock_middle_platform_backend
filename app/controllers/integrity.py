from fastapi import APIRouter, Depends
from app.core.deps import get_stock_data_service, require_permissions
from app.models.integrity import IntegrityCheckRequest, IntegrityCheckResponse
from app.models.user import User
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/integrity", tags=["数据完整性"])


@router.post(
    "/check",
    response_model=IntegrityCheckResponse,
    summary="校验 K 线数据完整性",
    description="传入股票代码和时间范围，返回服务端的记录统计，以便客户端比对。",
)
async def check_data_integrity(
    payload: IntegrityCheckRequest,
    _: User = Depends(require_permissions(["stocks:read"])),
    service: StockDataService = Depends(get_stock_data_service),
) -> IntegrityCheckResponse:
    results = await service.check_integrity(payload)
    return IntegrityCheckResponse(results=results)
