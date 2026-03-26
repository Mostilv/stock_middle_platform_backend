import json

from decouple import config


def _cast_debug(value):
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on", "debug", "dev", "development"}:
        return True
    if text in {"0", "false", "no", "off", "release", "prod", "production"}:
        return False
    raise ValueError(f"Invalid truth value: {value}")


class Settings:
    project_name: str = config("APP_NAME", default="Stock Middle Platform Backend")
    debug: bool = config("DEBUG", default=True, cast=_cast_debug)
    api_v1_str: str = "/api/v1"
    version: str = config("APP_VERSION", default="1.0.0")
    description: str = config(
        "APP_DESCRIPTION",
        default="Stock data analysis and strategy management platform",
    )

    mongodb_url: str = config("MONGODB_URL", default="mongodb://localhost:27017")
    use_mock_db: bool = config("USE_MOCK_DB", default=False, cast=bool)
    mongodb_db: str = (
        f"{config('MONGODB_DB', default='stock_platform')}_mock"
        if use_mock_db
        else config("MONGODB_DB", default="stock_platform")
    )

    secret_key: str = config("SECRET_KEY", default="your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int
    )

    cors_origins: list[str] = ["*"]

    log_level: str = config("LOG_LEVEL", default="INFO")
    bcrypt_rounds: int = config("BCRYPT_ROUNDS", default=12, cast=int)

    def __init__(self):
        data_targets_raw = config("DATA_TARGETS", default="")
        if data_targets_raw:
            try:
                parsed = json.loads(data_targets_raw)
            except json.JSONDecodeError as exc:
                raise ValueError("DATA_TARGETS must be valid JSON") from exc
        else:
            parsed = {
                "stock_basic": {
                    "primary": {
                        "database": self.mongodb_db,
                        "collection": "stock_basic",
                        "description": "Normalized stock basic information",
                    }
                },
                "stock_kline": {
                    "primary": {
                        "database": self.mongodb_db,
                        "collection": "stock_kline",
                        "description": "Normalized stock k-line records",
                    }
                },
                "indicator": {
                    "primary": {
                        "database": self.mongodb_db,
                        "collection": "indicator_data",
                        "description": "Calculated indicator records",
                    }
                },
            }
        if not isinstance(parsed, dict):
            raise ValueError("DATA_TARGETS must be a mapping")
        self.data_targets = parsed


settings = Settings()
