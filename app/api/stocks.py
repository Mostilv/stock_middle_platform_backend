from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.stock_data_service import StockDataService

router = APIRouter(prefix="/stocks", tags=["股票数据"])


class MinuteIngestRequest(BaseModel):
    """分钟级数据抓取请求体"""

    start_date: date = Field(..., description="开始日期，格式YYYY-MM-DD")
    end_date: date = Field(..., description="结束日期，格式YYYY-MM-DD")


class FundamentalIngestRequest(BaseModel):
    """基本面数据抓取请求体"""

    start_date: date = Field(..., description="开始日期，格式YYYY-MM-DD")
    end_date: date = Field(..., description="结束日期，格式YYYY-MM-DD")


class DailyReconcileRequest(BaseModel):
    """日线数据对账任务请求体"""

    lookback_trading_days: int = Field(
        7,
        ge=1,
        le=60,
        description="回溯交易日数量，默认7天",
    )
    threshold: Optional[float] = Field(
        None,
        ge=0,
        description="关键字段允许的绝对百分比误差，默认使用系统配置",
    )
    full_history_start: Optional[date] = Field(
        None,
        description="全量刷新时的起始日期，默认使用1990-01-01",
    )


@router.post("/{code}/minute", summary="抓取1分钟K线数据")
async def ingest_minute_data(
    code: str,
    request: MinuteIngestRequest,
    _: User = Depends(get_current_active_user),
    service: StockDataService = Depends(),
):
    try:
        modified = await service.ingest_minute_bars(code, request.start_date, request.end_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return {
        "code": code,
        "frequency": "1m",
        "start_date": request.start_date,
        "end_date": request.end_date,
        "modified": modified,
    }


@router.post("/{code}/fundamental", summary="抓取基本面数据")
async def ingest_fundamental_data(
    code: str,
    request: FundamentalIngestRequest,
    _: User = Depends(get_current_active_user),
    service: StockDataService = Depends(),
):
    try:
        modified = await service.ingest_fundamental_data(code, request.start_date, request.end_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return {
        "code": code,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "modified": modified,
    }


@router.post("/{code}/daily/reconcile", summary="校验并刷新日线数据")
async def reconcile_daily_data(
    code: str,
    request: DailyReconcileRequest,
    _: User = Depends(get_current_active_user),
    service: StockDataService = Depends(),
):
    try:
        result = await service.reconcile_recent_daily_bars(
            code,
            lookback_trading_days=request.lookback_trading_days,
            threshold=request.threshold,
            full_history_start=request.full_history_start,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return result
