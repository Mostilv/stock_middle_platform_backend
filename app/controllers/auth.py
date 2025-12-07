from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.core.deps import (
    get_current_active_user,
    get_settings_service,
    get_user_service,
)
from app.core.security import create_access_token
from app.models.auth_payloads import LoginRequest, LoginResponse, LoginUser
from app.services.user_service import UserService
from app.models.user import User, UserCreate
from app.services.frontend_state_service import SettingsService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=User)
async def register(
    user_create: UserCreate, user_service: UserService = Depends(get_user_service)
):
    """用户注册"""
    try:
        user = await user_service.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    user_service: UserService = Depends(get_user_service),
    settings_service: SettingsService = Depends(get_settings_service),
):
    """用户登录"""
    await user_service.ensure_default_admin()
    user = await user_service.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    settings_data = await settings_service.get_settings(user.username)
    return LoginResponse(
        token=access_token,
        user=LoginUser(
            username=user.username,
            role="admin" if user.is_superuser else "user",
            email=user.email,
            displayName=user.display_name or user.username,
            avatarUrl=user.avatar_url,
            emailConfigs=settings_data.emailConfigs,
            notificationTemplates=settings_data.notificationTemplates,
        ),
    )


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user
