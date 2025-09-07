#!/usr/bin/env python3
"""
创建MySQL表结构脚本
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.user import Base as UserBase
from app.models.role import Base as RoleBase


def create_tables():
    """创建数据库表"""
    try:
        # 创建数据库连接
        database_url = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}"
        engine = create_engine(database_url, echo=True)
        
        # 创建所有表
        UserBase.metadata.create_all(engine)
        RoleBase.metadata.create_all(engine)
        
        print("数据库表创建成功！")
        
        # 创建默认权限
        create_default_permissions(engine)
        
    except Exception as e:
        print(f"创建表失败: {e}")


def create_default_permissions(engine):
    """创建默认权限"""
    try:
        with engine.connect() as conn:
            # 插入默认权限
            permissions = [
                ("users:read", "用户读取权限"),
                ("users:write", "用户写入权限"),
                ("roles:read", "角色读取权限"),
                ("roles:write", "角色写入权限"),
                ("strategies:read", "策略读取权限"),
                ("strategies:write", "策略写入权限"),
                ("indicators:read", "指标读取权限"),
                ("indicators:write", "指标写入权限"),
                ("portfolio:read", "组合读取权限"),
                ("portfolio:write", "组合写入权限"),
            ]
            
            for perm_name, perm_desc in permissions:
                # 检查权限是否已存在
                result = conn.execute(text("SELECT id FROM permissions WHERE name = :name"), {"name": perm_name})
                if not result.fetchone():
                    conn.execute(
                        text("INSERT INTO permissions (name, description) VALUES (:name, :description)"),
                        {"name": perm_name, "description": perm_desc}
                    )
                    print(f"创建权限: {perm_name}")
            
            # 创建默认角色
            result = conn.execute(text("SELECT id FROM roles WHERE name = 'admin'"))
            if not result.fetchone():
                conn.execute(
                    text("INSERT INTO roles (name, description) VALUES ('admin', '系统管理员')"),
                )
                print("创建角色: admin")
            
            result = conn.execute(text("SELECT id FROM roles WHERE name = 'user'"))
            if not result.fetchone():
                conn.execute(
                    text("INSERT INTO roles (name, description) VALUES ('user', '普通用户')"),
                )
                print("创建角色: user")
            
            conn.commit()
            print("默认权限和角色创建成功！")
            
    except Exception as e:
        print(f"创建默认权限失败: {e}")


if __name__ == "__main__":
    create_tables()
