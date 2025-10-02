import os
from decouple import config
from typing import Optional


class Settings:
    # 应用基本配置
    app_name: str = config("APP_NAME", default="股票中间平台后端")
    debug: bool = config("DEBUG", default=True, cast=bool)
    
    # Swagger文档配置
    swagger_ui_parameters = {
        "defaultModelsExpandDepth": -1,  # 隐藏模型部分
        "defaultModelExpandDepth": 3,    # 模型展开深度
        "docExpansion": "list",          # 默认展开方式
        "filter": True,                  # 启用搜索过滤
        "showExtensions": True,          # 显示扩展信息
        "showCommonExtensions": True,    # 显示通用扩展
        "syntaxHighlight.theme": "monokai",  # 代码高亮主题
        "tryItOutEnabled": True,         # 启用"Try it out"功能
    }
    
    # API配置
    api_v1_str: str = "/api/v1"
    project_name: str = "股票中间平台后端"
    version: str = "1.00"
    description: str = "专业的股票数据分析和策略管理平台"
    
    # 数据库配置
    # MongoDB配置
    mongodb_url: str = config("MONGODB_URL", default="mongodb://localhost:27017")
    mongodb_db: str = config("MONGODB_DB", default="stock_platform")
    
    # MySQL配置
    mysql_host: str = config("MYSQL_HOST", default="localhost")
    mysql_port: int = config("MYSQL_PORT", default=3306, cast=int)
    mysql_user: str = config("MYSQL_USER", default="root")
    mysql_password: str = config("MYSQL_PASSWORD", default="")
    mysql_database: str = config("MYSQL_DATABASE", default="stock_platform")
    mysql_charset: str = config("MYSQL_CHARSET", default="utf8mb4")
    
    # 数据库连接池配置
    mysql_pool_size: int = config("MYSQL_POOL_SIZE", default=10, cast=int)
    mysql_max_overflow: int = config("MYSQL_MAX_OVERFLOW", default=20, cast=int)
    mysql_pool_timeout: int = config("MYSQL_POOL_TIMEOUT", default=30, cast=int)
    mysql_pool_recycle: int = config("MYSQL_POOL_RECYCLE", default=3600, cast=int)
    
    # JWT配置
    secret_key: str = config("SECRET_KEY", default="your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 跨域配置
    cors_origins: list = ["*"]
    
    # 日志配置
    log_level: str = config("LOG_LEVEL", default="INFO")
    
    # 安全配置
    bcrypt_rounds: int = 12
    
    # 股票数据源配置
    baostock_user: str = config("BAOSTOCK_USER", default="anonymous")
    baostock_password: str = config("BAOSTOCK_PASSWORD", default="123456")

    # 股票数据日线对账配置
    stock_daily_anomaly_threshold: float = config(
        "STOCK_DAILY_ANOMALY_THRESHOLD", default=0.005, cast=float
    )

    # 聚宽平台配置
    joinquant_username: str = config("JOINQUANT_USERNAME", default="")
    joinquant_password: str = config("JOINQUANT_PASSWORD", default="")
    joinquant_webhook_secret: str = config("JOINQUANT_WEBHOOK_SECRET", default="")

settings = Settings()
