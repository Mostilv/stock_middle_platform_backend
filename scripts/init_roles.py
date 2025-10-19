#!/usr/bin/env python3
"""��ʼ��Ĭ�Ͻ�ɫ��Ȩ�޽ű�"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import mongodb
from app.services.role_service import RoleService
from app.models.role import RoleCreate


DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "ϵͳ����Ա",
        "permissions": [
            "users:read",
            "users:write",
            "roles:read",
            "roles:write",
            "strategies:read",
            "strategies:write",
            "indicators:read",
            "indicators:write",
        ],
    },
    {
        "name": "user",
        "description": "��ͨ�û�",
        "permissions": [
            "strategies:read",
            "indicators:read",
        ],
    },
]


async def init_roles():
    await mongodb.connect_to_mongo()
    service = RoleService()
    try:
        for role in DEFAULT_ROLES:
            existing = await service.get_role_by_name(role["name"])
            if existing:
                print(f"��ɫ�Ѵ��ڣ�����: {role['name']}")
                continue
            await service.create_role(role_create=RoleCreate(**role))
            print(f"������ɫ�ɹ�: {role['name']}")
    finally:
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(init_roles())
