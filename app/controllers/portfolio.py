from fastapi import APIRouter, Depends

from app.core.deps import get_optional_active_user, get_portfolio_service
from app.models.portfolio import PortfolioOverview
from app.models.user import User
from app.services.frontend_state_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["投资组合"])


@router.get("/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(
    _: User = Depends(get_optional_active_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.get_overview()
