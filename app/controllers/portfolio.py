from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_active_user, get_current_superuser, get_portfolio_service
from app.models.portfolio import PortfolioOverview
from app.models.user import User
from app.services.frontend_state_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["投资组合"])


@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(
    _: User = Depends(get_current_active_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.get_overview()


@router.post("/strategies/{strategy_id}/toggle")
async def toggle_strategy(
    strategy_id: str,
    active: bool = Query(..., description="是否启动策略"),
    _: User = Depends(get_current_superuser),
    service: PortfolioService = Depends(get_portfolio_service),
):
    await service.toggle_strategy_status(strategy_id, active)
    return {"ok": True}
