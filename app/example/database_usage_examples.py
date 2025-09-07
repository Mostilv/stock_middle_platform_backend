"""
数据库使用示例
展示如何使用新的数据库连接模块进行MySQL和MongoDB操作
"""

import asyncio
from datetime import datetime
from app.db import db_manager, data_access, MySQLDataAccess, MongoDBDataAccess

async def mysql_examples():
    """MySQL操作示例"""
    print("=== MySQL操作示例 ===")
    
    # 1. 执行查询
    try:
        # 查询所有表
        tables = await MySQLDataAccess.get_table_list()
        print(f"数据库中的表: {[table['table_name'] for table in tables]}")
        
        # 执行自定义查询
        result = await MySQLDataAccess.execute_query(
            "SELECT DATABASE() as current_db, NOW() as current_time",
            fetch_one=True
        )
        print(f"当前数据库和时间: {result}")
        
    except Exception as e:
        print(f"MySQL查询失败: {e}")
    
    # 2. 插入数据示例（需要先创建表）
    try:
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS test_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await MySQLDataAccess.execute_query(create_table_sql)
        print("✅ 测试表创建成功")
        
        # 插入数据
        user_id = await MySQLDataAccess.insert_data(
            "test_users",
            {
                "username": "test_user",
                "email": "test@example.com"
            },
            return_id=True
        )
        print(f"✅ 用户插入成功，ID: {user_id}")
        
        # 查询插入的数据
        users = await MySQLDataAccess.execute_query(
            "SELECT * FROM test_users WHERE id = :user_id",
            {"user_id": user_id}
        )
        print(f"查询到的用户: {users}")
        
        # 更新数据
        updated_rows = await MySQLDataAccess.update_data(
            "test_users",
            {"email": "updated@example.com"},
            "id = :user_id",
            {"user_id": user_id}
        )
        print(f"✅ 更新了 {updated_rows} 行数据")
        
        # 删除数据
        deleted_rows = await MySQLDataAccess.delete_data(
            "test_users",
            "id = :user_id",
            {"user_id": user_id}
        )
        print(f"✅ 删除了 {deleted_rows} 行数据")
        
    except Exception as e:
        print(f"MySQL操作失败: {e}")

async def mongodb_examples():
    """MongoDB操作示例"""
    print("\n=== MongoDB操作示例 ===")
    
    try:
        # 1. 插入文档
        user_doc = {
            "username": "mongodb_user",
            "email": "mongodb@example.com",
            "profile": {
                "age": 25,
                "city": "北京"
            },
            "tags": ["developer", "python", "mongodb"]
        }
        
        doc_id = await MongoDBDataAccess.insert_document("test_users", user_doc)
        print(f"✅ 文档插入成功，ID: {doc_id}")
        
        # 2. 查询文档
        users = await MongoDBDataAccess.find_documents(
            "test_users",
            {"username": "mongodb_user"}
        )
        print(f"查询到的用户: {users}")
        
        # 3. 更新文档
        updated_count = await MongoDBDataAccess.update_document(
            "test_users",
            {"username": "mongodb_user"},
            {"$set": {"email": "updated_mongodb@example.com"}}
        )
        print(f"✅ 更新了 {updated_count} 个文档")
        
        # 4. 批量插入
        batch_docs = [
            {"username": f"user_{i}", "email": f"user{i}@example.com"}
            for i in range(1, 4)
        ]
        inserted_ids = await MongoDBDataAccess.insert_many_documents("test_users", batch_docs)
        print(f"✅ 批量插入了 {len(inserted_ids)} 个文档")
        
        # 5. 统计文档数量
        count = await MongoDBDataAccess.count_documents("test_users")
        print(f"集合中的文档总数: {count}")
        
        # 6. 创建索引
        index_name = await MongoDBDataAccess.create_index(
            "test_users",
            [("username", 1)],
            unique=True
        )
        print(f"✅ 创建索引: {index_name}")
        
        # 7. 删除文档
        deleted_count = await MongoDBDataAccess.delete_many_documents(
            "test_users",
            {"username": {"$regex": "^user_"}}
        )
        print(f"✅ 删除了 {deleted_count} 个文档")
        
    except Exception as e:
        print(f"MongoDB操作失败: {e}")

async def database_manager_examples():
    """数据库管理器示例"""
    print("\n=== 数据库管理器示例 ===")
    
    try:
        # 1. 获取MySQL会话
        async with db_manager.get_mysql_session() as session:
            result = await session.execute("SELECT 'Hello MySQL' as message")
            row = result.fetchone()
            print(f"MySQL会话测试: {row[0] if row else 'No result'}")
        
        # 2. 获取MongoDB集合
        collection = db_manager.get_mongodb_collection("test_collection")
        # 测试集合操作
        await collection.insert_one({"test": "Hello MongoDB"})
        doc = await collection.find_one({"test": "Hello MongoDB"})
        print(f"MongoDB集合测试: {doc}")
        await collection.delete_one({"test": "Hello MongoDB"})
        
    except Exception as e:
        print(f"数据库管理器操作失败: {e}")

async def health_check_example():
    """健康检查示例"""
    print("\n=== 健康检查示例 ===")
    
    try:
        health_status = await data_access.health_check()
        print(f"数据库健康状态: {health_status}")
        
        # 检查连接状态
        is_connected = db_manager._connected
        print(f"数据库连接状态: {is_connected}")
        
    except Exception as e:
        print(f"健康检查失败: {e}")

async def main():
    """主函数 - 运行所有示例"""
    print("🚀 开始数据库操作示例...")
    
    # 确保数据库已连接
    if not db_manager._connected:
        print("正在连接数据库...")
        await db_manager.connect_all()
    
    # 运行示例
    await mysql_examples()
    await mongodb_examples()
    await database_manager_examples()
    await health_check_example()
    
    print("\n✅ 所有示例执行完成！")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
