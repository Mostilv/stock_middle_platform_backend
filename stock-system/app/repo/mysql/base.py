from __future__ import annotations
from __future__ import annotations

from typing import AsyncIterator, Callable


class DummySession:
    pass


async def init_engine() -> None:
    return None


def get_sessionmaker() -> Callable[[], "SessionContext"]:
    return SessionContext


class SessionContext:
    def __init__(self) -> None:
        self._session = DummySession()

    async def __aenter__(self) -> DummySession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


async def get_session() -> AsyncIterator[DummySession]:
    async with SessionContext() as session:
        yield session


async def dispose_engine() -> None:
    return None


__all__ = ["init_engine", "get_session", "get_sessionmaker", "dispose_engine", "DummySession"]
