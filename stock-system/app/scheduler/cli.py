from __future__ import annotations

import argparse
import asyncio

from .jobs import create_scheduler, job_compute_indicators, job_refresh_daily, job_send_mail
from ..main import create_app


async def run_once(app, name: str) -> None:
    if name == "daily":
        await job_refresh_daily(app)
        await job_compute_indicators(app)
        await job_send_mail(app)
    else:
        raise ValueError(f"Unknown job set: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock system scheduler")
    parser.add_argument("--once", choices=["daily"], help="Run once and exit", dest="once")
    args = parser.parse_args()

    app = create_app()

    loop = asyncio.get_event_loop()

    async def startup() -> None:
        for handler in app.router.on_startup:
            await handler()

    async def shutdown() -> None:
        for handler in app.router.on_shutdown:
            await handler()

    async def runner() -> None:
        await startup()
        if args.once:
            await run_once(app, args.once)
        else:
            scheduler = create_scheduler(app)
            scheduler.start()
            try:
                await asyncio.Event().wait()
            finally:
                scheduler.shutdown(wait=False)
        await shutdown()

    loop.run_until_complete(runner())


if __name__ == "__main__":
    main()
