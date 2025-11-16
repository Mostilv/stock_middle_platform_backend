from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import (
    get_industry_analytics_service,
    require_permissions,
)
from app.models.analytics import IndustryMetricResponse
from app.models.user import User
from app.services.industry_analytics_service import IndustryAnalyticsService

router = APIRouter(prefix="/analytics", tags=["行业分析"])


@router.get(
    "/industry/metrics",
    response_model=IndustryMetricResponse,
    summary="查询行业动量/宽度指标",
    description="聚合 indicator 数据，返回行业动量与行业宽度的时间序列结果。",
)
async def fetch_industry_metrics(
    indicator: str = Query(
        "industry_metrics", description="指标标识，默认 industry_metrics"
    ),
    target: str = Query("primary", description="使用的数据目标别名"),
    timeframe: str = Query("1d", description="时间粒度，仅支持 1d"),
    days: int = Query(12, ge=1, le=120, description="返回的交易日数量"),
    end: Optional[datetime] = Query(
        None, description="可选的结束时间（UTC），默认当前时间"
    ),
    _: User = Depends(require_permissions(["indicators:read"])),
    service: IndustryAnalyticsService = Depends(get_industry_analytics_service),
) -> IndustryMetricResponse:
    try:
        return await service.get_industry_metrics(
            indicator=indicator,
            target=target,
            timeframe=timeframe,
            days=days,
            end=end,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询行业指标失败: {exc}",
        ) from exc
