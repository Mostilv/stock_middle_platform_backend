# 数据库连接模块使用指南

## 概述

本项目新增了完整的数据库连接模块，支持MySQL和MongoDB的双数据库架构，提供了统一的数据库访问接口和连接管理功能。

## 主要特性

- ✅ **双数据库支持**: 同时支持MySQL和MongoDB
- ✅ **连接池管理**: MySQL连接池配置和自动管理
- ✅ **异步操作**: 完全异步的数据库操作
- ✅ **生命周期管理**: 自动处理应用启动和关闭时的数据库连接
- ✅ **健康检查**: 实时监控数据库连接状态
- ✅ **错误处理**: 完善的异常处理和日志记录
- ✅ **向后兼容**: 保持与现有代码的兼容性

## 文件结构

```
app/
├── db/                         # 数据库模块
│   ├── __init__.py            # 模块初始化
│   ├── database.py            # 数据库连接管理器
│   ├── database_manager.py    # 应用生命周期管理器
│   └── database_utils.py      # 数据访问工具类
└── example/                    # 示例模块
    ├── __init__.py            # 模块初始化
    ├── database_usage_examples.py  # 使用示例
    └── DATABASE_MODULE_GUIDE.md    # 使用指南
```

## 配置说明

### 环境变量配置

在 `.env` 文件中配置数据库连接参数：

```env
# MongoDB配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=stock_platform

# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=stock_platform
MYSQL_CHARSET=utf8mb4

# MySQL连接池配置
MYSQL_POOL_SIZE=10
MYSQL_MAX_OVERFLOW=20
MYSQL_POOL_TIMEOUT=30
MYSQL_POOL_RECYCLE=3600
```

### 依赖包

确保安装了以下依赖包：

```txt
sqlalchemy==2.0.23
pymysql==1.1.0
aiomysql==0.2.0
motor==3.3.2
pymongo==4.6.0
```

## 使用方法

### 1. 基本使用

#### MySQL操作

```python
from app.db import MySQLDataAccess

# 执行查询
result = await MySQLDataAccess.execute_query(
    "SELECT * FROM users WHERE id = :user_id",
    {"user_id": 1},
    fetch_one=True
)

# 插入数据
user_id = await MySQLDataAccess.insert_data(
    "users",
    {"username": "test", "email": "test@example.com"},
    return_id=True
)

# 更新数据
updated_rows = await MySQLDataAccess.update_data(
    "users",
    {"email": "new@example.com"},
    "id = :user_id",
    {"user_id": user_id}
)

# 删除数据
deleted_rows = await MySQLDataAccess.delete_data(
    "users",
    "id = :user_id",
    {"user_id": user_id}
)
```

#### MongoDB操作

```python
from app.db import MongoDBDataAccess

# 插入文档
doc_id = await MongoDBDataAccess.insert_document(
    "users",
    {"username": "test", "email": "test@example.com"}
)

# 查询文档
users = await MongoDBDataAccess.find_documents(
    "users",
    {"username": "test"}
)

# 更新文档
updated_count = await MongoDBDataAccess.update_document(
    "users",
    {"username": "test"},
    {"$set": {"email": "new@example.com"}}
)

# 删除文档
deleted_count = await MongoDBDataAccess.delete_document(
    "users",
    {"username": "test"}
)
```

### 2. 高级使用

#### 使用数据库管理器

```python
from app.db import db_manager

# 获取MySQL会话
async with db_manager.get_mysql_session() as session:
    result = await session.execute("SELECT * FROM users")
    users = result.fetchall()

# 获取MongoDB集合
collection = db_manager.get_mongodb_collection("users")
await collection.insert_one({"username": "test"})
```

#### 健康检查

```python
from app.db import data_access

# 检查数据库健康状态
health_status = await data_access.health_check()
print(health_status)  # {'mysql': True, 'mongodb': True}
```

### 3. 在API中使用

```python
from fastapi import APIRouter, Depends
from app.db import db_manager
from app.db import MySQLDataAccess

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    # 使用MySQL查询用户
    user = await MySQLDataAccess.execute_query(
        "SELECT * FROM users WHERE id = :user_id",
        {"user_id": user_id},
        fetch_one=True
    )
    
    if not user:
        return {"error": "用户不存在"}
    
    return {"user": user}
```

## 应用集成

### 自动生命周期管理

应用已经集成了自动的数据库生命周期管理：

```python
# app/main.py
from app.db import lifespan

app = FastAPI(
    # ... 其他配置
    lifespan=lifespan  # 自动管理数据库连接
)
```

### 健康检查端点

访问 `/health` 端点可以查看数据库连接状态：

```json
{
    "status": "healthy",
    "database": {
        "mysql": true,
        "mongodb": true
    },
    "connected": true
}
```

## 最佳实践

### 1. 错误处理

```python
try:
    result = await MySQLDataAccess.execute_query(query, params)
except Exception as e:
    logger.error(f"数据库操作失败: {e}")
    # 处理错误
```

### 2. 连接管理

- 使用上下文管理器自动管理连接
- 避免长时间持有数据库连接
- 定期检查连接健康状态

### 3. 性能优化

- 使用连接池减少连接开销
- 合理设置连接池参数
- 使用索引优化查询性能

### 4. 安全考虑

- 使用参数化查询防止SQL注入
- 不要在日志中记录敏感信息
- 定期更新数据库密码

## 故障排除

### 常见问题

1. **连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数是否正确
   - 检查网络连接

2. **性能问题**
   - 调整连接池大小
   - 检查查询是否使用了索引
   - 监控数据库性能指标

3. **内存泄漏**
   - 确保正确关闭数据库连接
   - 检查是否有未释放的资源

### 调试技巧

1. 启用SQLAlchemy日志：
```python
# 在config.py中设置
debug: bool = True
```

2. 使用健康检查监控连接状态

3. 查看应用日志获取详细错误信息

## 示例代码

完整的使用示例请参考 `app/examples/database_usage_examples.py` 文件。

## 更新日志

- **v1.0.0**: 初始版本，支持MySQL和MongoDB双数据库
- 添加了连接池管理
- 实现了异步操作支持
- 集成了生命周期管理
- 提供了完整的工具类

## 技术支持

如有问题，请查看：
1. 应用日志文件
2. 数据库连接状态
3. 环境变量配置
4. 依赖包版本
