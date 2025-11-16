#!/usr/bin/env python3
"""初始化默认角色与权限的脚本。"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import mongodb
from app.models.role import RoleCreate
from app.services.role_service import RoleService


DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "系统管理员",
        "permissions": [
            "users:read",
            "users:write",
            "roles:read",
            "roles:write",
            "strategies:read",
            "strategies:write",
            "indicators:read",
            "indicators:write",
            "stocks:read",
            "stocks:write",
        ],
    },
    {
        "name": "user",
        "description": "普通用户",
        "permissions": [
            "strategies:read",
            "indicators:read",
            "stocks:read",
        ],
    },
]


async def init_roles() -> None:
    await mongodb.connect_to_mongo()
    service = RoleService()
    try:
        for role in DEFAULT_ROLES:
            existing = await service.get_role_by_name(role["name"])
            if existing:
                print(f"角色已存在，跳过: {role['name']}")
                continue
            await service.create_role(role_create=RoleCreate(**role))
            print(f"创建角色成功: {role['name']}")
    finally:
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(init_roles())
