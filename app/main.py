from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from app.config import settings
from app.db import mongodb, lifespan, db_connection_manager
from app.api import auth, users, strategies, indicators
from app.api import roles
from app.utils.swagger_config import (
    get_custom_openapi,
    get_swagger_ui_parameters,
    get_api_tags,
    get_servers
)

# 创建FastAPI应用
app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "股票中间平台开发组",
        "email": "dev@stockplatform.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=get_servers(),
    tags=get_api_tags(),
    lifespan=lifespan  # 添加生命周期管理器
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix=settings.api_v1_str, tags=["认证"])
app.include_router(users.router, prefix=settings.api_v1_str, tags=["用户管理"])
app.include_router(roles.router, prefix=settings.api_v1_str, tags=["用户管理"])
app.include_router(strategies.router, prefix=settings.api_v1_str, tags=["策略管理"])
app.include_router(indicators.router, prefix=settings.api_v1_str, tags=["技术指标"])

# 自定义OpenAPI配置
app.openapi = lambda: get_custom_openapi(app, app.title, app.version, app.description)

# 自定义Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_ui_parameters=get_swagger_ui_parameters(),
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

# 注意：startup和shutdown事件现在由lifespan管理器处理
# 如果需要额外的启动逻辑，可以在lifespan函数中添加

@app.get("/", tags=["系统监控"])
async def root():
    """根路径 - 测试热更新功能"""
    return {
        "message": f"🎯 {settings.project_name} - 热重载实时生效！",
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "timestamp": "2024-09-04 23:58:00",
        "status": "⚡ 热重载功能实时生效",
        "feature": "修改代码后自动重载，无需重启服务",
        "server": "Uvicorn + FastAPI",
        "monitoring": "监控目录: app/, scripts/",
        "hot_reload": "实时监控文件变化"
    }

@app.get("/health", tags=["系统监控"])
async def health_check():
    """健康检查接口"""
    # 获取数据库健康状态
    db_health = await db_connection_manager.health_check()
    
    return {
        "status": "healthy",
        "timestamp": "2024-09-04 23:58:00",
        "service": settings.project_name,
        "version": settings.version,
        "database": db_health,
        "connected": db_connection_manager.is_connected()
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )
