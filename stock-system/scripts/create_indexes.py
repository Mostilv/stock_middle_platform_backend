from __future__ import annotations

import asyncio

from app.repo.mysql import base as mysql_base


async def main() -> None:
    await mysql_base.init_engine()


if __name__ == "__main__":
    asyncio.run(main())
