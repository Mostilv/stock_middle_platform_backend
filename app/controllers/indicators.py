from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/indicators", tags=["指标展示"])


@router.get("/stocks")
async def get_stock_list(
    source: str = Query("akshare", description="数据源 akshare 或 baostock"),
    service: IndicatorService = Depends(),
):
    """获取股票列表（无需认证）"""
    try:
        return await service.get_stock_list(source)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("/stocks/{stock_code}")
async def get_stock_data(
    stock_code: str,
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    source: str = Query("akshare", description="数据源 akshare 或 baostock"),
    service: IndicatorService = Depends(),
):
    """获取股票历史数据（无需认证）"""
    try:
        return await service.get_stock_history(stock_code, start_date, end_date, source)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票数据失败: {exc}",
        ) from exc


@router.get("/stocks/{stock_code}/realtime")
async def get_stock_realtime(
    stock_code: str, service: IndicatorService = Depends()
):
    """获取股票实时数据（无需认证）"""
    try:
        return await service.get_stock_realtime(stock_code)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票实时数据失败: {exc}",
        ) from exc


@router.get("/indices/{index_code}")
async def get_index_data(
    index_code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    service: IndicatorService = Depends(),
):
    """获取指数数据（无需认证）"""
    try:
        return await service.get_index_data(index_code, start_date, end_date)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指数数据失败: {exc}",
        ) from exc


@router.get("/market/overview")
async def get_market_overview(service: IndicatorService = Depends()):
    """获取市场概览（无需认证）"""
    try:
        return await service.get_market_overview()
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取市场概览失败: {exc}",
        ) from exc
