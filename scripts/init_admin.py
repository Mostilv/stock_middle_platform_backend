#!/usr/bin/env python3
"""
初始化管理员用户脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import mongodb
from app.services.user_service import UserService


async def create_superuser():
    """创建超级用户"""
    try:
        # 连接数据库
        await mongodb.connect_to_mongo()
        
        # 创建用户服务
        user_service = UserService()
        
        # 检查是否已存在超级用户
        existing_admin = await user_service.get_user_by_username("admin")
        if existing_admin:
            print("超级用户已存在，跳过创建")
            return
        
        # 创建超级用户
        admin_user = await user_service.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin123",
            full_name="系统管理员"
        )
        
        print(f"超级用户创建成功: {admin_user.username}")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"密码: admin123")
        print("请及时修改默认密码！")
        
    except Exception as e:
        print(f"创建超级用户失败: {e}")
    finally:
        # 关闭数据库连接
        await mongodb.close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_superuser())
