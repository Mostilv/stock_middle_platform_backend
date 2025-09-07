import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self):
        self.mysql_engine = None
        self.mysql_async_engine = None
        self.mysql_session_factory = None
        self.mysql_async_session_factory = None
        self.mongodb_client = None
        self.mongodb_db = None
        self._connected = False
    
    async def connect_mysql(self):
        """连接MySQL数据库"""
        try:
            # 同步MySQL连接
            mysql_url = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset={settings.mysql_charset}"
            self.mysql_engine = create_engine(
                mysql_url,
                poolclass=QueuePool,
                pool_size=settings.mysql_pool_size,
                max_overflow=settings.mysql_max_overflow,
                pool_timeout=settings.mysql_pool_timeout,
                pool_recycle=settings.mysql_pool_recycle,
                echo=settings.debug
            )
            
            # 异步MySQL连接
            mysql_async_url = f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset={settings.mysql_charset}"
            self.mysql_async_engine = create_async_engine(
                mysql_async_url,
                pool_size=settings.mysql_pool_size,
                max_overflow=settings.mysql_max_overflow,
                pool_timeout=settings.mysql_pool_timeout,
                pool_recycle=settings.mysql_pool_recycle,
                echo=settings.debug
            )
            
            # 创建会话工厂
            self.mysql_session_factory = sessionmaker(bind=self.mysql_engine)
            self.mysql_async_session_factory = async_sessionmaker(
                bind=self.mysql_async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("✅ 已连接到MySQL数据库")
            return True
            
        except Exception as e:
            logger.error(f"❌ MySQL连接失败: {e}")
            return False
    
    async def connect_mongodb(self):
        """连接MongoDB数据库"""
        try:
            self.mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
            self.mongodb_db = self.mongodb_client[settings.mongodb_db]
            
            # 测试连接
            await self.mongodb_client.admin.command('ping')
            logger.info("✅ 已连接到MongoDB数据库")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB连接失败: {e}")
            return False
    
    async def connect_all(self):
        """连接所有数据库"""
        mysql_connected = await self.connect_mysql()
        mongodb_connected = await self.connect_mongodb()
        
        self._connected = mysql_connected and mongodb_connected
        return self._connected
    
    async def disconnect_all(self):
        """断开所有数据库连接"""
        try:
            if self.mysql_async_engine:
                await self.mysql_async_engine.dispose()
                logger.info("🔌 已断开MySQL异步连接")
            
            if self.mysql_engine:
                self.mysql_engine.dispose()
                logger.info("🔌 已断开MySQL同步连接")
            
            if self.mongodb_client:
                self.mongodb_client.close()
                logger.info("🔌 已断开MongoDB连接")
            
            self._connected = False
            
        except Exception as e:
            logger.error(f"❌ 断开数据库连接时出错: {e}")
    
    @asynccontextmanager
    async def get_mysql_session(self):
        """获取MySQL异步会话上下文管理器"""
        if not self.mysql_async_session_factory:
            raise RuntimeError("MySQL未连接")
        
        async with self.mysql_async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_mysql_sync_session(self):
        """获取MySQL同步会话"""
        if not self.mysql_session_factory:
            raise RuntimeError("MySQL未连接")
        return self.mysql_session_factory()
    
    def get_mongodb_collection(self, collection_name: str):
        """获取MongoDB集合"""
        if not self.mongodb_db:
            raise RuntimeError("MongoDB未连接")
        return self.mongodb_db[collection_name]

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 向后兼容的MongoDB类
class MongoDB:
    """向后兼容的MongoDB类"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect_to_mongo(self):
        """连接到MongoDB"""
        success = await db_manager.connect_mongodb()
        if success:
            self.client = db_manager.mongodb_client
            self.db = db_manager.mongodb_db
        return success
    
    async def close_mongo_connection(self):
        """关闭MongoDB连接"""
        if self.client:
            self.client.close()
            logger.info("🔌 已断开MongoDB连接")

# 向后兼容的实例
mongodb = MongoDB()
