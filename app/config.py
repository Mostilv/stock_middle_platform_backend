from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "股票中间平台"
    debug: bool = True
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # MongoDB配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "stock_platform"
    
    # MySQL配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_db: str = "stock_data"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 数据源配置
    baostock_user: str = "anonymous"
    baostock_password: str = "123456"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
