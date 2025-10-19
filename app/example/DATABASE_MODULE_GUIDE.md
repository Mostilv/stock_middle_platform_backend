# 数据库模块简明指南

项目中的数据库模块已经收敛为一个轻量的 MongoDB 管理器。下面的内容概述了可用组件以及如何在业务代码里使用它们。

## 模块结构

```
app/
├── db/
│   ├── __init__.py
│   ├── database.py          # DatabaseManager 与兼容层
│   └── database_manager.py  # FastAPI lifespan 帮助函数
└── example/
    ├── __init__.py
    └── database_usage_examples.py  # 简单的 MongoDB 使用示例
```

## 快速开始

```python
from app.db import db_manager

async def create_demo_record():
    await db_manager.connect_all()  # 启动时通常由 lifespan 自动完成

    collection = db_manager.get_mongodb_collection("demo_logs")
    await collection.insert_one({"message": "hello", "level": "info"})

    health = await db_manager.health_check()
    print(health)  # {'mongodb': True}
```

> 提示：如果应用通过 `FastAPI(lifespan=lifespan)` 启动，则无需手动调用 `connect_all`/`disconnect_all`。

## DatabaseManager 能力

| 方法 | 说明 |
| ---- | ---- |
| `connect_all()` | 建立 MongoDB 连接，供应用启动时调用 |
| `disconnect_all()` | 关闭现有连接，应用优雅退出时调用 |
| `health_check()` | 返回 `{"mongodb": bool}`，可用于健康检查 |
| `get_mongodb_collection(name)` | 返回指定集合对象，常用于业务服务 |
| `is_connected()` | 返回最近一次连接结果 |

同时保留了 `mongodb` 兼容层，仍可通过 `from app.db import mongodb` 获取 `mongodb.db` 与 `mongodb.client`。

## 健康检查

`DatabaseConnectionManager` 封装在 `database_manager.py` 内，FastAPI 的 `/health` 端点会使用它来查询数据库状态。独立使用时：

```python
from app.db import db_connection_manager

status = await db_connection_manager.health_check()
if all(status.values()):
    print("数据库正常")
```

## 示例脚本

`app/example/database_usage_examples.py` 提供了一个最小示例，演示了插入文档、读取最新记录以及输出健康检查结果。可通过 `python app/example/database_usage_examples.py` 直接运行。

## 常见问题

- **连接失败**：确认 MongoDB 服务是否运行，以及 `MONGODB_URL`、`MONGODB_DB` 环境变量是否配置正确。
- **首次访问报错**：确保在访问 `db_manager` 之前已经建立连接（通常由 lifespan 自动处理）。
- **需要不同的数据库**：如果后续扩展到其他数据库，可在 `DatabaseManager` 中按需新增连接逻辑。
