from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_account_service, get_optional_active_user
from app.models.account import (
    AccountProfile,
    AccountProfileUpdate,
    PasswordChangeRequest,
)
from app.models.user import User
from app.services.frontend_state_service import AccountService

router = APIRouter(prefix="/account", tags=["账户与系统设置"])


@router.get("/profile", response_model=AccountProfile)
async def get_profile(
    current_user: User = Depends(get_optional_active_user),
    service: AccountService = Depends(get_account_service),
):
    return await service.get_profile(current_user)


@router.put("/profile", response_model=AccountProfile)
async def update_profile(
    payload: AccountProfileUpdate,
    current_user: User = Depends(get_optional_active_user),
    service: AccountService = Depends(get_account_service),
):
    return await service.update_profile(current_user, payload)


@router.post("/password")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_optional_active_user),
    service: AccountService = Depends(get_account_service),
):
    try:
        await service.change_password(current_user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return {"ok": True}
