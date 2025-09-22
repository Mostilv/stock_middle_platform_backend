from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status

from ..config import get_settings
from ..repo.mysql import base as mysql_base
from ..service.data_refresh_service import DataRefreshService
from ..service.fundamentals_service import FundamentalsService
from ..service.indicator_service import IndicatorService
from ..service.jq_bridge_service import JQBridgeService
from ..service.mail_service import MailService
from ..service.rebalance_service import RebalanceService


async def require_api_key(api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    settings = get_settings()
    if api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")


async def get_db_session() -> AsyncIterator[object]:
    async for session in mysql_base.get_session():
        yield session


def get_data_service(request: Request) -> DataRefreshService:
    return request.app.state.data_service


def get_indicator_service(request: Request) -> IndicatorService:
    return request.app.state.indicator_service


def get_mail_service(request: Request) -> MailService:
    return request.app.state.mail_service


def get_jq_service(request: Request) -> JQBridgeService:
    return request.app.state.jq_service


def get_rebalance_service(request: Request) -> RebalanceService:
    return request.app.state.rebalance_service


def get_fundamentals_service(request: Request) -> FundamentalsService:
    return request.app.state.fundamentals_service


__all__ = [
    "require_api_key",
    "get_db_session",
    "get_data_service",
    "get_indicator_service",
    "get_mail_service",
    "get_jq_service",
    "get_rebalance_service",
    "get_fundamentals_service",
]
