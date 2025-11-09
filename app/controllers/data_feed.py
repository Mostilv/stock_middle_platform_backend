from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user, get_qlib_data_service
from app.models.qlib import QlibIngestSummary, QlibStockBatch
from app.models.user import User
from app.services.qlib_data_service import QlibDataIngestionService

router = APIRouter(prefix="/data", tags=["数据接入"])


@router.post(
    "/qlib/bars",
    response_model=QlibIngestSummary,
    status_code=status.HTTP_200_OK,
    summary="上传符合 qlib 股票格式的数据",
    description=(
        "接受与 qlib 官方股票日线/分钟线格式一致的数据，"
        "通过身份认证后写入 MongoDB，供本项目及量化组件使用。"
    ),
)
async def ingest_qlib_stock_bars(
    payload: QlibStockBatch,
    _: User = Depends(get_current_active_user),
    service: QlibDataIngestionService = Depends(get_qlib_data_service),
) -> QlibIngestSummary:
    """Receive qlib-formatted stock bars from external data pipelines."""

    try:
        return await service.ingest_batch(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入股票数据失败: {exc}",
        ) from exc
