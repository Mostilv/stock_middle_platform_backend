from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers import auth, data_feed, indicators, roles, strategies, users
from app.config import settings
from app.db import db_connection_manager, lifespan
from app.utils.swagger_config import (
    get_api_tags,
    get_custom_openapi,
    get_servers,
)

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "股票中间平台开发组", "email": "dev@stockplatform.com"},
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

app.include_router(auth.router, prefix=settings.api_v1_str, tags=["认证"])
app.include_router(users.router, prefix=settings.api_v1_str, tags=["用户管理"])
app.include_router(roles.router, prefix=settings.api_v1_str, tags=["用户管理"])
app.include_router(strategies.router, prefix=settings.api_v1_str, tags=["策略管理"])
app.include_router(indicators.router, prefix=settings.api_v1_str, tags=["指标数据"])
app.include_router(data_feed.router, prefix=settings.api_v1_str, tags=["数据接入"])


def _custom_openapi():
    return get_custom_openapi(app, app.title, app.version, app.description)


app.openapi = _custom_openapi


@app.get("/", tags=["系统监控"])
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
    }


@app.get("/health", tags=["系统监控"])
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
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"服务器内部错误: {exc}"})
