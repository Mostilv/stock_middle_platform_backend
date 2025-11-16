from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import (
    get_stock_data_service,
    require_permissions,
)
from app.models.stock_data import (
    DataPushConfigResponse,
    DataWriteSummary,
    StockBasicBatch,
    StockKlineBatch,
)
from app.models.user import User
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/stocks", tags=["数据接入"])


@router.get(
    "/targets",
    response_model=DataPushConfigResponse,
    summary="查看可用数据目标",
    description="返回后端支持的股票基础/K线/指标推送目标及 JSON Schema 样例。",
)
async def list_stock_targets(
    _: User = Depends(require_permissions(["stocks:read"])),
    service: StockDataService = Depends(get_stock_data_service),
) -> DataPushConfigResponse:
    return service.describe_targets()


@router.post(
    "/basic",
    response_model=DataWriteSummary,
    status_code=status.HTTP_200_OK,
    summary="推送股票基础信息",
    description="接受 AStock 等数据源整理后的股票基础资料，并保存到配置的数据库目标中。",
)
async def ingest_stock_basic(
    payload: StockBasicBatch,
    _: User = Depends(require_permissions(["stocks:write"])),
    service: StockDataService = Depends(get_stock_data_service),
) -> DataWriteSummary:
    try:
        return await service.ingest_basic(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"股票基础数据格式错误: {exc}。请参考 /api/v1/stocks/targets 返回的 schema。",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入股票基础数据失败: {exc}",
        ) from exc


@router.post(
    "/kline",
    response_model=DataWriteSummary,
    status_code=status.HTTP_200_OK,
    summary="推送股票 K 线数据",
    description="批量写入日线、周线、月线、分钟线等 K 线数据，支持自定义目标数据库。",
)
async def ingest_stock_kline(
    payload: StockKlineBatch,
    _: User = Depends(require_permissions(["stocks:write"])),
    service: StockDataService = Depends(get_stock_data_service),
) -> DataWriteSummary:
    try:
        return await service.ingest_kline(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"K线数据格式错误: {exc}。请参考 /api/v1/stocks/targets 返回的 schema。",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入 K 线数据失败: {exc}",
        ) from exc
