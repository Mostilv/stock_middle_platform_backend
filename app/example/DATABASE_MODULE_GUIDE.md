# 数据库模块说明

后端当前使用 MongoDB，数据库连接相关代码位于 `app/db/`。

## 目录

```text
app/db/
|-- __init__.py
|-- database.py
`-- database_manager.py
```

## 主要能力

- 建立 MongoDB 连接
- 在应用关闭时断开连接
- 提供健康检查
- 返回指定集合对象

## 典型用法

```python
from app.db import db_manager

collection = db_manager.get_mongodb_collection("demo_logs")
```

在 FastAPI 正常通过 `lifespan` 启动时，连接初始化会自动完成。

## 示例脚本

可参考 `app/example/database_usage_examples.py`。
