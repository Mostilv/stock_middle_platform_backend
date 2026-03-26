from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user, get_qlib_data_service
from app.db.database import db_manager
from app.models.data_sync import (
    DataPushResponse,
    LimitUpPoolPushRequest,
    MarketIndicesPushRequest,
)
from app.models.qlib import QlibIngestSummary, QlibStockBatch
from app.models.user import User
from app.services.qlib_data_service import QlibDataIngestionService

router = APIRouter(prefix="/data", tags=["data"])


@router.post(
    "/qlib/bars",
    response_model=QlibIngestSummary,
    status_code=status.HTTP_200_OK,
    summary="Ingest qlib-formatted bars",
    description="Receive normalized qlib bar data and write it into MongoDB.",
)
async def ingest_qlib_stock_bars(
    payload: QlibStockBatch,
    _: User = Depends(get_current_active_user),
    service: QlibDataIngestionService = Depends(get_qlib_data_service),
) -> QlibIngestSummary:
    try:
        return await service.ingest_batch(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest qlib bar data: {exc}",
        ) from exc


@router.post(
    "/market/indices",
    response_model=DataPushResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest market index snapshot",
)
async def ingest_market_indices(
    payload: MarketIndicesPushRequest,
    _: User = Depends(get_current_active_user),
) -> DataPushResponse:
    try:
        database = db_manager.get_database(
            payload.target if payload.target != "primary" else None
        )
        collection = database["market_indices"]
        await collection.update_one(
            {"_id": "latest_indices"},
            {"$set": payload.data},
            upsert=True,
        )
        return DataPushResponse(ok=True, records_saved=len(payload.data))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest market indices: {exc}",
        ) from exc


@router.post(
    "/limit_up/pool",
    response_model=DataPushResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest daily limit-up pool",
)
async def ingest_limit_up_pool(
    payload: LimitUpPoolPushRequest,
    _: User = Depends(get_current_active_user),
) -> DataPushResponse:
    try:
        database = db_manager.get_database(
            payload.target if payload.target != "primary" else None
        )
        collection = database["limit_up_pool"]
        await collection.delete_many({"date": payload.date})

        records = []
        for item in payload.data:
            if hasattr(item, "model_dump"):
                records.append(item.model_dump())
            elif hasattr(item, "dict"):
                records.append(item.dict())
            else:
                records.append(item)

        if records:
            await collection.insert_many(records)

        return DataPushResponse(ok=True, records_saved=len(records))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest limit-up pool: {exc}",
        ) from exc
