"""
数据库连接管理器
负责应用启动和关闭时的数据库连接管理
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import db_manager
from .database_utils import data_access

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    负责数据库连接的启动和关闭
    """
    # 启动时连接数据库
    logger.info("🚀 正在启动数据库连接...")
    
    try:
        # 连接所有数据库
        connected = await db_manager.connect_all()
        
        if connected:
            logger.info("✅ 所有数据库连接成功")
            
            # 执行健康检查
            health_status = await data_access.health_check()
            logger.info(f"📊 数据库健康状态: {health_status}")
            
            # 将数据库管理器添加到应用状态
            app.state.db_manager = db_manager
            app.state.data_access = data_access
            
        else:
            logger.error("❌ 数据库连接失败")
            # 即使连接失败也继续启动，但记录错误
            
    except Exception as e:
        logger.error(f"❌ 数据库连接过程中发生错误: {e}")
    
    yield
    
    # 关闭时断开数据库连接
    logger.info("🔄 正在关闭数据库连接...")
    
    try:
        await db_manager.disconnect_all()
        logger.info("✅ 所有数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接时发生错误: {e}")

class DatabaseConnectionManager:
    """数据库连接管理器类"""
    
    def __init__(self):
        self.connected = False
        self.health_status = {}
    
    async def initialize(self) -> bool:
        """
        初始化数据库连接
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("🔧 正在初始化数据库连接...")
            
            # 连接所有数据库
            self.connected = await db_manager.connect_all()
            
            if self.connected:
                # 执行健康检查
                self.health_status = await data_access.health_check()
                logger.info(f"📊 数据库健康状态: {self.health_status}")
                return True
            else:
                logger.error("❌ 数据库连接失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            return False
    
    async def shutdown(self):
        """关闭数据库连接"""
        try:
            logger.info("🔄 正在关闭数据库连接...")
            await db_manager.disconnect_all()
            self.connected = False
            self.health_status = {}
            logger.info("✅ 数据库连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭数据库连接时发生错误: {e}")
    
    async def health_check(self) -> dict:
        """
        执行数据库健康检查
        
        Returns:
            健康状态字典
        """
        try:
            self.health_status = await data_access.health_check()
            return self.health_status
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {e}")
            return {"mysql": False, "mongodb": False}
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def get_health_status(self) -> dict:
        """获取健康状态"""
        return self.health_status

# 全局数据库连接管理器实例
db_connection_manager = DatabaseConnectionManager()
