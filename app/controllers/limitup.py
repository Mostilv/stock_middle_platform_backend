from fastapi import APIRouter, Depends, Query

from app.core.deps import get_limitup_service, get_optional_active_user
from app.models.limitup import LimitUpOverview
from app.models.user import User
from app.services.frontend_state_service import LimitUpService

router = APIRouter(prefix="/limitup", tags=["涨停监控"])


@router.get("/overview", response_model=LimitUpOverview)
async def get_limitup_overview(
    date: str | None = Query(
        None, description="交易日（YYYY-MM-DD），为空则返回最新记录"
    ),
    _: User = Depends(get_optional_active_user),
    service: LimitUpService = Depends(get_limitup_service),
):
    return await service.get_overview(date)
