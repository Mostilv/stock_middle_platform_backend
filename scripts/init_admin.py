#!/usr/bin/env python3
"""初始化管理员用户脚本"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import mongodb
from app.services.user_service import UserService


async def create_superuser():
    try:
        await mongodb.connect_to_mongo()
        user_service = UserService()

        existing_admin = await user_service.get_user_by_username("admin")
        if existing_admin:
            print("超级用户已存在，跳过创建")
            return

        admin_user = await user_service.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
            full_name="系统管理员",
        )

        print(f"超级用户创建成功: {admin_user.username}")
        print("用户名: admin")
        print("密码: admin123 (请尽快修改)")
        print(f"邮箱: {admin_user.email}")
    except Exception as exc:
        print(f"创建超级用户失败: {exc}")
    finally:
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_superuser())
