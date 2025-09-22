from __future__ import annotations

import logging

from fastapi import FastAPI

from .api import routes_fundamentals, routes_health, routes_indicators, routes_positions, routes_signals, routes_stocks, routes_tasks, routes_webhook_jq
from .api.routes_signals import rebalance_router
from .config import get_settings
from .repo.mongo import base as mongo_base
from .repo.mysql import base as mysql_base
from .service.data_refresh_service import DataRefreshService
from .service.fundamentals_service import FundamentalsService
from .service.indicator_service import IndicatorService
from .service.jq_bridge_service import JQBridgeService
from .service.mail_service import MailService
from .service.rebalance_service import RebalanceService
from .utils.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Stock System", version="0.1.0")
    app.state.settings = settings

    app.include_router(routes_health.router)
    app.include_router(routes_tasks.router)
    app.include_router(routes_webhook_jq.router)
    app.include_router(routes_positions.router)
    app.include_router(routes_signals.router)
    app.include_router(rebalance_router)
    app.include_router(routes_stocks.router)
    app.include_router(routes_indicators.router)
    app.include_router(routes_fundamentals.router)

    @app.on_event("startup")
    async def on_startup() -> None:
        configure_logging()
        logging.getLogger(__name__).info("Starting Stock System")
        await mysql_base.init_engine()
        session_factory = mysql_base.get_sessionmaker()
        app.state.session_factory = session_factory
        app.state.data_service = DataRefreshService()
        app.state.indicator_service = IndicatorService()
        app.state.mail_service = MailService()
        app.state.jq_service = JQBridgeService()
        app.state.rebalance_service = RebalanceService()
        app.state.fundamentals_service = FundamentalsService(app.state.data_service)

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await mysql_base.dispose_engine()
        await mongo_base.close_database()

    return app


app = create_app()


__all__ = ["app", "create_app"]
