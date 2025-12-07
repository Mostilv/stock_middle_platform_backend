from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import get_optional_active_user, get_subscription_service
from app.models.subscription import StrategySubscriptionState
from app.models.user import User
from app.services.frontend_state_service import StrategySubscriptionService

router = APIRouter(prefix="/strategies", tags=["策略订阅"])


class SubscriptionUpdate(BaseModel):
    strategyId: str
    subscribed: bool
    channels: list[str] | None = None


class BlacklistUpdate(BaseModel):
    blacklist: list[str]


@router.get("/subscriptions", response_model=StrategySubscriptionState)
async def list_subscriptions(
    current_user: User = Depends(get_optional_active_user),
    service: StrategySubscriptionService = Depends(get_subscription_service),
):
    return await service.get_state(current_user.username)


@router.post("/subscriptions")
async def update_subscription(
    payload: SubscriptionUpdate,
    current_user: User = Depends(get_optional_active_user),
    service: StrategySubscriptionService = Depends(get_subscription_service),
):
    if not payload.strategyId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="strategyId 不能为空"
        )
    await service.set_subscribed(
        current_user.username, payload.strategyId, payload.subscribed, payload.channels
    )
    return {"ok": True}


@router.post("/subscriptions/blacklist")
async def update_blacklist(
    payload: BlacklistUpdate,
    current_user: User = Depends(get_optional_active_user),
    service: StrategySubscriptionService = Depends(get_subscription_service),
):
    await service.update_blacklist(current_user.username, payload.blacklist)
    return {"ok": True}
