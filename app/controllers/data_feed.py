from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user, get_qlib_data_service
from app.models.qlib import QlibIngestSummary, QlibStockBatch
from app.models.data_sync import MarketIndicesPushRequest, LimitUpPoolPushRequest, DataPushResponse
from app.models.user import User
from app.services.qlib_data_service import QlibDataIngestionService
from app.db.database import db_manager

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

@router.post(
    "/market/indices",
    response_model=DataPushResponse,
    status_code=status.HTTP_200_OK,
    summary="推送核心市场指数",
)
async def ingest_market_indices(
    payload: MarketIndicesPushRequest,
    _: User = Depends(get_current_active_user),
) -> DataPushResponse:
    try:
        db = db_manager.get_database(payload.target if payload.target != "primary" else None)
        col = db["market_indices"]
        
        # Save historical indices in a single document for easy retrieval
        # Or upsert individual index docs. The easiest is a single document for internal platform
        # since it's just the 'latest' snapshot required by the web dashboard
        await col.update_one(
            {"_id": "latest_indices"},
            {"$set": payload.data},
            upsert=True
        )
        return DataPushResponse(ok=True, records_saved=len(payload.data))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入指数数据失败: {exc}",
        ) from exc

@router.post(
    "/limit_up/pool",
    response_model=DataPushResponse,
    status_code=status.HTTP_200_OK,
    summary="推送当日涨停板池",
)
async def ingest_limit_up_pool(
    payload: LimitUpPoolPushRequest,
    _: User = Depends(get_current_active_user),
) -> DataPushResponse:
    try:
        db = db_manager.get_database(payload.target if payload.target != "primary" else None)
        col = db["limit_up_pool"]
        
        date_str = payload.date
        
        # Clear existing data for this date and insert new ones
        await col.delete_many({"date": date_str})
        
        records = []
        for r in payload.data:
            if hasattr(r, "model_dump"):
                records.append(r.model_dump())
            elif hasattr(r, "dict"):
                records.append(r.dict())
            else:
                records.append(r)
        
        if records:
            await col.insert_many(records)
            
        return DataPushResponse(ok=True, records_saved=len(records))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入涨停板数据失败: {exc}",
        ) from exc

