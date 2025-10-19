"""
简化示例：展示如何在项目中使用 DatabaseManager。
"""

import asyncio
from datetime import datetime

from app.db import db_manager


async def demo() -> None:
    await db_manager.connect_all()
    collection = db_manager.get_mongodb_collection("demo_logs")

    await collection.insert_one(
        {"message": "数据库连接正常", "created_at": datetime.utcnow()}
    )
    latest = await collection.find().sort("created_at", -1).to_list(length=5)
    print("最近记录:", latest)

    health = await db_manager.health_check()
    print("数据库健康情况:", health)

    await db_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(demo())
