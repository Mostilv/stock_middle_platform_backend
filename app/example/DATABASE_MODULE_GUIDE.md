# 数据库模块简明指南

项目已统一为轻量版 MongoDB 管理器，便于在服务启动和业务逻辑中复用。

## 目录结构
```
app/
├── db/
│   ├── __init__.py
│   ├── database.py           # DatabaseManager 与兼容层
│   └── database_manager.py   # FastAPI lifespan 助手
└── example/
    ├── __init__.py
    └── database_usage_examples.py  # MongoDB 使用示例
```

## 快速使用
```python
from app.db import db_manager

async def create_demo_record():
    await db_manager.connect_all()  # 若通过 lifespan 启动可省略

    collection = db_manager.get_mongodb_collection("demo_logs")
    await collection.insert_one({"message": "hello", "level": "info"})

    health = await db_manager.health_check()
    print(health)  # {'mongodb': True}
```

> 通过 `FastAPI(lifespan=lifespan)` 启动服务时，会自动调用 `connect_all` / `disconnect_all`。

## DatabaseManager 能力

| 方法 | 说明 |
| --- | --- |
| `connect_all()` | 建立 MongoDB 连接 |
| `disconnect_all()` | 优雅关闭连接 |
| `health_check()` | 返回 `{"mongodb": bool}`，可用于 `/health` |
| `get_mongodb_collection(name)` | 获取指定集合实例 |
| `is_connected()` | 返回最近一次连接状态 |

同时保留 `mongodb` 兼容层，可 `from app.db import mongodb` 获取 `mongodb.db`、`mongodb.client`。

## 健康检查
`DatabaseConnectionManager` 封装在 `database_manager.py`，`/health` 会调用：

```python
from app.db import db_connection_manager

status = await db_connection_manager.health_check()
if all(status.values()):
    print("数据库正常")
```

## 示例脚本
`app/example/database_usage_examples.py` 演示插入文档、读取最新记录与健康检查，可直接运行：
```bash
python app/example/database_usage_examples.py
```

## 常见问题
- **连接失败**：检查 MongoDB 服务是否启动，以及 `MONGODB_URL`、`MONGODB_DB` 是否正确。
- **首次访问出错**：确保在访问 `db_manager` 前已建立连接（通常由 lifespan 自动完成）。
- **多数据源需求**：可在 `DatabaseManager` 中增加新的连接逻辑并对外暴露 getter。
