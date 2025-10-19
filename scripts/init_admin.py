#!/usr/bin/env python3
"""��ʼ������Ա�û��ű�"""

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
            print("�����û��Ѵ��ڣ���������")
            return

        admin_user = await user_service.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
            full_name="ϵͳ����Ա",
        )

        print(f"�����û������ɹ�: {admin_user.username}")
        print("�û���: admin")
        print("����: admin123 (�뾡���޸�)")
        print(f"����: {admin_user.email}")
    except Exception as exc:
        print(f"���������û�ʧ��: {exc}")
    finally:
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_superuser())
