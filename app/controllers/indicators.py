from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_indicator_service, require_permissions
from app.models.indicator import (
    IndicatorPushRequest,
    IndicatorQueryResponse,
    IndicatorWriteSummary,
)
from app.models.user import User
from app.services.indicator_service import IndicatorService

router = APIRouter(prefix="/indicators", tags=["指标数据"])


@router.post(
    "/records",
    response_model=IndicatorWriteSummary,
    status_code=status.HTTP_200_OK,
    summary="推送指标数据",
    description="接收外部指标计算服务推送的批量结果，写入 MongoDB。",
)
async def push_indicator_records(
    payload: IndicatorPushRequest,
    _: User = Depends(require_permissions(["indicators:write"])),
    service: IndicatorService = Depends(get_indicator_service),
) -> IndicatorWriteSummary:
    """写入外部推送的指标数据"""
    try:
        return await service.ingest(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"指标数据格式错误: {exc}。schema 示例见 /api/v1/stocks/targets。",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入指标数据失败: {exc}",
        ) from exc


@router.get(
    "/records",
    response_model=IndicatorQueryResponse,
    summary="查询指标数据",
    description="按照指标标识、股票代码、时间范围等条件查询已经落库的指标内容。",
)
async def query_indicator_records(
    indicator: str = Query(..., description="指标标识，例如 rsi14"),
    symbol: Optional[str] = Query(None, description="股票代码，例如 SH600519"),
    timeframe: Optional[str] = Query(None, description="时间粒度，默认 1d"),
    start: Optional[datetime] = Query(
        None, description="开始时间（ISO8601），为空则不限制"
    ),
    end: Optional[datetime] = Query(
        None, description="结束时间（ISO8601），为空则不限制"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="返回的记录数上限，默认 100，最大 500",
    ),
    skip: int = Query(0, ge=0, description="跳过的记录数，支持分页"),
    tags: Optional[List[str]] = Query(
        None, description="按标签筛选，支持多次传参，如 ?tags=long&tags=demo"
    ),
    target: str = Query("primary", description="查询的数据目标别名，默认为 primary"),
    _: User = Depends(require_permissions(["indicators:read"])),
    service: IndicatorService = Depends(get_indicator_service),
) -> IndicatorQueryResponse:
    """查询已保存的指标结果"""
    try:
        return await service.query(
            indicator=indicator,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
            skip=skip,
            tags=tags,
            target=target,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询指标数据失败: {exc}",
        ) from exc
