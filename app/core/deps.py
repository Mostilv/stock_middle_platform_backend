from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.data_sinks import data_sink_registry
from app.core.security import verify_token
from app.models.user import User
from app.services.indicator_service import IndicatorService
from app.services.industry_analytics_service import IndustryAnalyticsService
from app.services.qlib_data_service import QlibDataIngestionService
from app.services.role_service import RoleService
from app.services.frontend_state_service import (
    AccountService,
    LimitUpService,
    MarketDataService,
    PortfolioService,
    SettingsService,
    StrategySubscriptionService,
)
from app.services.stock_data_service import StockDataService
from app.services.strategy_service import StrategyService
from app.services.user_service import UserService

security = HTTPBearer(scheme_name="BearerAuth")
optional_security = HTTPBearer(scheme_name="OptionalBearerAuth", auto_error=False)


def get_user_service() -> UserService:
    return UserService()


def get_role_service() -> RoleService:
    return RoleService()


def get_indicator_service() -> IndicatorService:
    return IndicatorService(registry=data_sink_registry)


def get_strategy_service() -> StrategyService:
    return StrategyService()


def get_qlib_data_service() -> QlibDataIngestionService:
    return QlibDataIngestionService()


def get_stock_data_service() -> StockDataService:
    return StockDataService(registry=data_sink_registry)


def get_industry_analytics_service() -> IndustryAnalyticsService:
    return IndustryAnalyticsService(registry=data_sink_registry)


def get_settings_service() -> SettingsService:
    return SettingsService()


def get_market_data_service() -> MarketDataService:
    return MarketDataService()


def get_limitup_service() -> LimitUpService:
    return LimitUpService()


def get_portfolio_service() -> PortfolioService:
    return PortfolioService()


def get_subscription_service() -> StrategySubscriptionService:
    return StrategySubscriptionService()


def get_account_service() -> AccountService:
    return AccountService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise credentials_exception

    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    Return the authenticated user when a bearer token is supplied; otherwise fall back
    to a demo admin user so the front-end can operate without Authorization headers.
    """
    if credentials and credentials.credentials:
        username = verify_token(credentials.credentials)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无法验证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await user_service.get_user_by_username(username)
        if user:
            return user
    return await user_service.ensure_default_admin()


async def get_optional_active_user(
    current_user: User = Depends(get_optional_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
        )
    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return current_user


def require_roles(required_roles: List[str]):
    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = set(current_user.roles or [])
        if not set(required_roles).issubset(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要角色: " + ",".join(required_roles),
            )
        return current_user

    return dependency


def require_permissions(required_permissions: List[str]):
    async def dependency(
        current_user: User = Depends(get_current_active_user),
        role_service: RoleService = Depends(get_role_service),
    ) -> User:
        # 合并用户直接权限与角色权限
        effective_permissions = set(current_user.permissions or [])
        for role_name in current_user.roles or []:
            role = await role_service.get_role_by_name(role_name)
            if role:
                effective_permissions.update(role.permissions or [])
        if not set(required_permissions).issubset(effective_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要权限: " + ",".join(required_permissions),
            )
        return current_user

    return dependency
