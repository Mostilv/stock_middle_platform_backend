from __future__ import annotations

from dataclasses import dataclass


def APIKeyHeader(name: str, auto_error: bool = True):  # type: ignore
    @dataclass
    class _APIKeyHeader:
        header_name: str = name
        auto_error: bool = auto_error

        def __call__(self, *args, **kwargs):
            return None

    return _APIKeyHeader()


__all__ = ["APIKeyHeader"]
