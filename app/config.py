from decouple import config


class Settings:
    project_name: str = config("APP_NAME", default="股票中间平台后端")
    debug: bool = config("DEBUG", default=True, cast=bool)
    api_v1_str: str = "/api/v1"
    version: str = config("APP_VERSION", default="1.0.0")
    description: str = config("APP_DESCRIPTION", default="股票数据分析与策略管理平台")

    mongodb_url: str = config("MONGODB_URL", default="mongodb://localhost:27017")
    mongodb_db: str = config("MONGODB_DB", default="stock_platform")

    secret_key: str = config("SECRET_KEY", default="your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int
    )

    cors_origins: list[str] = ["*"]

    log_level: str = config("LOG_LEVEL", default="INFO")
    bcrypt_rounds: int = config("BCRYPT_ROUNDS", default=12, cast=int)

    baostock_user: str = config("BAOSTOCK_USER", default="anonymous")
    baostock_password: str = config("BAOSTOCK_PASSWORD", default="123456")


settings = Settings()
