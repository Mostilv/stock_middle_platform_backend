"""
数据库工具类
提供MySQL和MongoDB的基础数据获取功能
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import json
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from .database import db_manager

logger = logging.getLogger(__name__)

class MySQLDataAccess:
    """MySQL数据访问工具类"""
    
    @staticmethod
    async def execute_query(
        query: str, 
        params: Optional[Dict] = None,
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Union[Dict, List[Dict], None]:
        """
        执行MySQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只获取一条记录
            fetch_all: 是否获取所有记录
            
        Returns:
            查询结果
        """
        try:
            async with db_manager.get_mysql_session() as session:
                result = await session.execute(text(query), params or {})
                
                if fetch_one:
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                elif fetch_all:
                    rows = result.fetchall()
                    return [dict(row._mapping) for row in rows]
                else:
                    return result.rowcount
                    
        except Exception as e:
            logger.error(f"MySQL查询执行失败: {e}")
            raise
    
    @staticmethod
    async def insert_data(
        table: str, 
        data: Dict[str, Any],
        return_id: bool = False
    ) -> Union[int, None]:
        """
        插入数据到MySQL表
        
        Args:
            table: 表名
            data: 要插入的数据
            return_id: 是否返回插入的ID
            
        Returns:
            插入的ID或None
        """
        try:
            async with db_manager.get_mysql_session() as session:
                # 构建插入语句
                columns = ', '.join(data.keys())
                placeholders = ', '.join([f':{key}' for key in data.keys()])
                query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                
                if return_id:
                    query += "; SELECT LAST_INSERT_ID() as id"
                    result = await session.execute(text(query), data)
                    row = result.fetchone()
                    await session.commit()
                    return row.id if row else None
                else:
                    result = await session.execute(text(query), data)
                    await session.commit()
                    return result.rowcount
                    
        except Exception as e:
            logger.error(f"MySQL数据插入失败: {e}")
            raise
    
    @staticmethod
    async def update_data(
        table: str, 
        data: Dict[str, Any], 
        where_clause: str,
        where_params: Optional[Dict] = None
    ) -> int:
        """
        更新MySQL表数据
        
        Args:
            table: 表名
            data: 要更新的数据
            where_clause: WHERE条件
            where_params: WHERE条件参数
            
        Returns:
            影响的行数
        """
        try:
            async with db_manager.get_mysql_session() as session:
                # 构建更新语句
                set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
                query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                
                # 合并参数
                params = {**data, **(where_params or {})}
                
                result = await session.execute(text(query), params)
                await session.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"MySQL数据更新失败: {e}")
            raise
    
    @staticmethod
    async def delete_data(
        table: str, 
        where_clause: str,
        where_params: Optional[Dict] = None
    ) -> int:
        """
        删除MySQL表数据
        
        Args:
            table: 表名
            where_clause: WHERE条件
            where_params: WHERE条件参数
            
        Returns:
            影响的行数
        """
        try:
            async with db_manager.get_mysql_session() as session:
                query = f"DELETE FROM {table} WHERE {where_clause}"
                result = await session.execute(text(query), where_params or {})
                await session.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"MySQL数据删除失败: {e}")
            raise
    
    @staticmethod
    async def get_table_info(table: str) -> List[Dict]:
        """
        获取表结构信息
        
        Args:
            table: 表名
            
        Returns:
            表结构信息
        """
        query = """
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as column_default,
            COLUMN_KEY as column_key,
            EXTRA as extra,
            COLUMN_COMMENT as column_comment
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
        ORDER BY ORDINAL_POSITION
        """
        return await MySQLDataAccess.execute_query(query, {"table_name": table})
    
    @staticmethod
    async def get_table_list() -> List[Dict]:
        """
        获取数据库中的所有表
        
        Returns:
            表列表
        """
        query = """
        SELECT 
            TABLE_NAME as table_name,
            TABLE_COMMENT as table_comment,
            CREATE_TIME as create_time,
            UPDATE_TIME as update_time
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME
        """
        return await MySQLDataAccess.execute_query(query)

class MongoDBDataAccess:
    """MongoDB数据访问工具类"""
    
    @staticmethod
    def get_collection(collection_name: str) -> AsyncIOMotorCollection:
        """
        获取MongoDB集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            MongoDB集合对象
        """
        return db_manager.get_mongodb_collection(collection_name)
    
    @staticmethod
    async def find_documents(
        collection_name: str,
        filter_dict: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Dict]:
        """
        查找MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            projection: 字段投影
            sort: 排序条件 [(field, direction), ...]
            limit: 限制数量
            skip: 跳过数量
            
        Returns:
            文档列表
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            cursor = collection.find(filter_dict or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc in cursor:
                # 处理ObjectId和日期类型
                doc = MongoDBDataAccess._serialize_document(doc)
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"MongoDB文档查找失败: {e}")
            raise
    
    @staticmethod
    async def find_one_document(
        collection_name: str,
        filter_dict: Optional[Dict] = None,
        projection: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        查找单个MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            projection: 字段投影
            
        Returns:
            文档或None
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            doc = await collection.find_one(filter_dict or {}, projection)
            
            if doc:
                return MongoDBDataAccess._serialize_document(doc)
            return None
            
        except Exception as e:
            logger.error(f"MongoDB单文档查找失败: {e}")
            raise
    
    @staticmethod
    async def insert_document(
        collection_name: str,
        document: Dict[str, Any]
    ) -> str:
        """
        插入MongoDB文档
        
        Args:
            collection_name: 集合名称
            document: 要插入的文档
            
        Returns:
            插入的文档ID
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            # 添加创建时间
            document['created_at'] = datetime.utcnow()
            document['updated_at'] = datetime.utcnow()
            
            result = await collection.insert_one(document)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"MongoDB文档插入失败: {e}")
            raise
    
    @staticmethod
    async def insert_many_documents(
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量插入MongoDB文档
        
        Args:
            collection_name: 集合名称
            documents: 要插入的文档列表
            
        Returns:
            插入的文档ID列表
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            
            # 为每个文档添加时间戳
            current_time = datetime.utcnow()
            for doc in documents:
                doc['created_at'] = current_time
                doc['updated_at'] = current_time
            
            result = await collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"MongoDB批量文档插入失败: {e}")
            raise
    
    @staticmethod
    async def update_document(
        collection_name: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False
    ) -> int:
        """
        更新MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            update_dict: 更新内容
            upsert: 是否在不存在时插入
            
        Returns:
            修改的文档数量
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            
            # 添加更新时间
            update_dict['$set'] = update_dict.get('$set', {})
            update_dict['$set']['updated_at'] = datetime.utcnow()
            
            result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
            return result.modified_count
            
        except Exception as e:
            logger.error(f"MongoDB文档更新失败: {e}")
            raise
    
    @staticmethod
    async def update_many_documents(
        collection_name: str,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any]
    ) -> int:
        """
        批量更新MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            update_dict: 更新内容
            
        Returns:
            修改的文档数量
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            
            # 添加更新时间
            update_dict['$set'] = update_dict.get('$set', {})
            update_dict['$set']['updated_at'] = datetime.utcnow()
            
            result = await collection.update_many(filter_dict, update_dict)
            return result.modified_count
            
        except Exception as e:
            logger.error(f"MongoDB批量文档更新失败: {e}")
            raise
    
    @staticmethod
    async def delete_document(
        collection_name: str,
        filter_dict: Dict[str, Any]
    ) -> int:
        """
        删除MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            删除的文档数量
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            result = await collection.delete_one(filter_dict)
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"MongoDB文档删除失败: {e}")
            raise
    
    @staticmethod
    async def delete_many_documents(
        collection_name: str,
        filter_dict: Dict[str, Any]
    ) -> int:
        """
        批量删除MongoDB文档
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            删除的文档数量
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            result = await collection.delete_many(filter_dict)
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"MongoDB批量文档删除失败: {e}")
            raise
    
    @staticmethod
    async def count_documents(
        collection_name: str,
        filter_dict: Optional[Dict] = None
    ) -> int:
        """
        统计MongoDB文档数量
        
        Args:
            collection_name: 集合名称
            filter_dict: 查询条件
            
        Returns:
            文档数量
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            return await collection.count_documents(filter_dict or {})
            
        except Exception as e:
            logger.error(f"MongoDB文档统计失败: {e}")
            raise
    
    @staticmethod
    async def create_index(
        collection_name: str,
        index_spec: Union[str, List[tuple]],
        **kwargs
    ) -> str:
        """
        创建MongoDB索引
        
        Args:
            collection_name: 集合名称
            index_spec: 索引规范
            **kwargs: 其他索引选项
            
        Returns:
            索引名称
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            result = await collection.create_index(index_spec, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"MongoDB索引创建失败: {e}")
            raise
    
    @staticmethod
    async def get_collection_info(collection_name: str) -> Dict:
        """
        获取集合信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            集合信息
        """
        try:
            collection = MongoDBDataAccess.get_collection(collection_name)
            stats = await collection.database.command("collStats", collection_name)
            return stats
            
        except Exception as e:
            logger.error(f"获取MongoDB集合信息失败: {e}")
            raise
    
    @staticmethod
    def _serialize_document(doc: Dict) -> Dict:
        """
        序列化MongoDB文档，处理特殊类型
        
        Args:
            doc: 原始文档
            
        Returns:
            序列化后的文档
        """
        if not doc:
            return doc
        
        # 处理ObjectId
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        # 处理日期类型
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, date):
                doc[key] = value.isoformat()
            elif isinstance(value, Decimal):
                doc[key] = float(value)
        
        return doc

class DataAccessManager:
    """数据访问管理器，统一管理MySQL和MongoDB操作"""
    
    def __init__(self):
        self.mysql = MySQLDataAccess()
        self.mongodb = MongoDBDataAccess()
    
    async def health_check(self) -> Dict[str, bool]:
        """
        检查数据库连接健康状态
        
        Returns:
            各数据库连接状态
        """
        health_status = {
            'mysql': False,
            'mongodb': False
        }
        
        try:
            # 检查MySQL连接
            result = await self.mysql.execute_query("SELECT 1 as test", fetch_one=True)
            health_status['mysql'] = result is not None
        except Exception as e:
            logger.error(f"MySQL健康检查失败: {e}")
        
        try:
            # 检查MongoDB连接
            collection = self.mongodb.get_collection('_health_check')
            await collection.database.command('ping')
            health_status['mongodb'] = True
        except Exception as e:
            logger.error(f"MongoDB健康检查失败: {e}")
        
        return health_status

# 全局数据访问管理器实例
data_access = DataAccessManager()
