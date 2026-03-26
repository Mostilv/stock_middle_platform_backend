from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.controllers import (
    account,
    analytics,
    auth,
    data_feed,
    indicators,
    integrity,
    limitup,
    market,
    portfolio,
    roles,
    settings as settings_controller,
    stocks,
    strategies,
    strategy_subscriptions,
    users,
)
from app.db import db_connection_manager, lifespan
from app.utils.swagger_config import get_api_tags, get_custom_openapi, get_servers

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Stock Platform Backend", "email": "dev@stockplatform.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    servers=get_servers(),
    tags=get_api_tags(),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(roles.router, prefix=settings.api_v1_str)
app.include_router(strategy_subscriptions.router, prefix=settings.api_v1_str)
app.include_router(strategies.router, prefix=settings.api_v1_str)
app.include_router(indicators.router, prefix=settings.api_v1_str)
app.include_router(data_feed.router, prefix=settings.api_v1_str)
app.include_router(stocks.router, prefix=settings.api_v1_str)
app.include_router(integrity.router, prefix=settings.api_v1_str)
app.include_router(analytics.router, prefix=settings.api_v1_str)
app.include_router(account.router, prefix=settings.api_v1_str)
app.include_router(settings_controller.router, prefix=settings.api_v1_str)
app.include_router(market.router, prefix=settings.api_v1_str)
app.include_router(limitup.router, prefix=settings.api_v1_str)
app.include_router(portfolio.router, prefix=settings.api_v1_str)


def _custom_openapi():
    return get_custom_openapi(app, app.title, app.version, app.description)


app.openapi = _custom_openapi


@app.get("/", tags=["system"])
async def root():
    database_status = await db_connection_manager.health_check()
    return {
        "service": settings.project_name,
        "version": settings.version,
        "docs": app.docs_url,
        "redoc": app.redoc_url,
        "openapi": app.openapi_url,
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
        "connected": db_connection_manager.is_connected(),
        "mongodb_db": settings.mongodb_db,
        "use_mock_db": settings.use_mock_db,
    }


@app.get("/health", tags=["system"])
async def health_check():
    database_status = await db_connection_manager.health_check()
    is_healthy = all(database_status.values()) if database_status else False
    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.project_name,
        "version": settings.version,
        "database": database_status,
        "connected": db_connection_manager.is_connected(),
        "mongodb_db": settings.mongodb_db,
        "use_mock_db": settings.use_mock_db,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )
