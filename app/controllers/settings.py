from fastapi import APIRouter, Depends

from app.core.deps import get_optional_active_user, get_settings_service
from app.models.settings import SettingsData
from app.models.user import User
from app.services.frontend_state_service import SettingsService

router = APIRouter(prefix="/settings", tags=["账户与系统设置"])


@router.get("/data", response_model=SettingsData)
async def fetch_settings_data(
    current_user: User = Depends(get_optional_active_user),
    service: SettingsService = Depends(get_settings_service),
):
    return await service.get_settings(current_user.username)


@router.post("/data")
async def save_settings_data(
    payload: SettingsData,
    current_user: User = Depends(get_optional_active_user),
    service: SettingsService = Depends(get_settings_service),
):
    await service.save_settings(current_user.username, payload)
    return {"ok": True}
