from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


DEFAULT_TZ = "Asia/Shanghai"


def now_tz(tz_name: str = DEFAULT_TZ) -> datetime:
    return datetime.now(tz=ZoneInfo(tz_name))


def parse_datetime(value: str, tz_name: str = DEFAULT_TZ) -> datetime:
    dt = datetime.fromisoformat(value)
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def format_date(value: datetime) -> str:
    return value.astimezone(ZoneInfo(DEFAULT_TZ)).strftime("%Y-%m-%d")


def format_datetime(value: datetime) -> str:
    return value.astimezone(ZoneInfo(DEFAULT_TZ)).isoformat(timespec="seconds")


__all__ = ["DEFAULT_TZ", "now_tz", "parse_datetime", "format_date", "format_datetime"]
