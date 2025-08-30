from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import mongodb
from app.api import auth, users, strategies, indicators

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="股票中间平台后端API",
    version="1.0.0",
    debug=settings.debug
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(strategies.router, prefix="/api/v1")
app.include_router(indicators.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    await mongodb.connect_to_mongo()
    print("应用启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    await mongodb.close_mongo_connection()
    print("应用关闭完成")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "股票中间平台后端API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )
