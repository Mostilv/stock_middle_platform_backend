from __future__ import annotations

import asyncio
from typing import List, Tuple

from fastapi import FastAPI


class SimpleScheduler:
    def __init__(self) -> None:
        self.jobs: List[Tuple] = []
        self._task: asyncio.Task | None = None

    def add_job(self, func, trigger: str, *, hour: int, minute: int, args: List, id: str) -> None:  # type: ignore[override]
        self.jobs.append((func, args))

    def start(self) -> None:
        async def runner() -> None:
            for func, args in self.jobs:
                await func(*args)
        self._task = asyncio.create_task(runner())

    def shutdown(self, wait: bool = False) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


async def job_refresh_daily(app: FastAPI) -> None:
    data_service = app.state.data_service
    await data_service.refresh_daily(["600519", "000001"], days=5)


async def job_compute_indicators(app: FastAPI) -> None:
    indicator_service = app.state.indicator_service
    await indicator_service.compute_builtin("600519", "MA", {"window": 5})
    await indicator_service.compute_builtin("600519", "RSI", {"window": 14})


async def job_send_mail(app: FastAPI) -> None:
    mail_service = app.state.mail_service
    session_factory = app.state.session_factory
    async with session_factory() as session:
        html = await mail_service.render_daily_mail(session)
        await mail_service.send_mail(session, html, [mail_service.settings.mail_to])


def create_scheduler(app: FastAPI) -> SimpleScheduler:
    scheduler = SimpleScheduler()
    scheduler.add_job(job_refresh_daily, "cron", hour=17, minute=30, args=[app], id="refresh")
    scheduler.add_job(job_compute_indicators, "cron", hour=17, minute=35, args=[app], id="indicators")
    scheduler.add_job(job_send_mail, "cron", hour=17, minute=40, args=[app], id="mail")
    return scheduler


__all__ = ["create_scheduler", "job_refresh_daily", "job_compute_indicators", "job_send_mail"]
