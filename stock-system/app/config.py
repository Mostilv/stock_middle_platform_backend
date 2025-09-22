from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.getenv("ENV", "dev"))
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", "dev-key"))
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret"))
    mysql_host: str = field(default_factory=lambda: os.getenv("MYSQL_HOST", "memory://"))
    mysql_port: int = field(default_factory=lambda: int(os.getenv("MYSQL_PORT", "3306")))
    mysql_db: str = field(default_factory=lambda: os.getenv("MYSQL_DB", "stocksys"))
    mysql_user: str = field(default_factory=lambda: os.getenv("MYSQL_USER", "stocks"))
    mysql_password: str = field(default_factory=lambda: os.getenv("MYSQL_PASSWORD", "stocks_pwd"))
    mongo_uri: str = field(default_factory=lambda: os.getenv("MONGO_URI", "memory://"))
    mongo_db: str = field(default_factory=lambda: os.getenv("MONGO_DB", "stocksys"))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.example.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "465")))
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", "noreply@example.com"))
    smtp_pass: str = field(default_factory=lambda: os.getenv("SMTP_PASS", "changeme"))
    mail_to: str = field(default_factory=lambda: os.getenv("MAIL_TO", "noreply@example.com"))
    tz: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Shanghai"))

    @property
    def mysql_async_url(self) -> str:
        return self.mysql_host


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
