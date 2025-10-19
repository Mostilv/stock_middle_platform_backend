# 股票中间平台后端

## 概览
- 基于 FastAPI 的股票中台后端，提供用户、角色、策略与指标管理能力。
- 现已统一使用 MongoDB 作为数据存储，移除了冗余的 MySQL 适配与数据访问层。
- 默认集成 JWT 鉴权、角色/权限校验以及 swagger 文档。

## 技术栈
- FastAPI + Uvicorn
- MongoDB（Motor 异步驱动）
- Redis / Celery（可选任务队列）
- Python-JOSE + Passlib（JWT 与密码哈希）

## 项目结构
```
|-- app
|   |-- __init__.py
|   |-- api
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- indicators.py
|   |   |-- roles.py
|   |   |-- strategies.py
|   |   +-- users.py
|   |-- config.py
|   |-- core
|   |   |-- __init__.py
|   |   |-- deps.py
|   |   +-- security.py
|   |-- db
|   |   |-- __init__.py
|   |   |-- database.py
|   |   +-- database_manager.py
|   |-- example
|   |   |-- __init__.py
|   |   |-- DATABASE_MODULE_GUIDE.md
|   |   +-- database_usage_examples.py
|   |-- main.py
|   |-- models
|   |   |-- __init__.py
|   |   |-- portfolio.py
|   |   |-- role.py
|   |   |-- strategy.py
|   |   +-- user.py
|   |-- services
|   |   |-- __init__.py
|   |   |-- role_service.py
|   |   |-- strategy_service.py
|   |   +-- user_service.py
|   +-- utils
|       |-- __init__.py
|       |-- data_sources.py
|       +-- swagger_config.py
|-- scripts
|   |-- init_admin.py
|   +-- init_roles.py
|-- env.example
|-- requirements.txt
|-- run.py / start.{bat,sh}
|-- docker-compose.yml / Dockerfile
|-- SWAGGER_GUIDE.md / SWAGGER_INTEGRATION_SUMMARY.md
|-- test_api.py / test_swagger*.py
|-- uvicorn_config.py
```

> 目录中保留了 `stock-system/` 作为配套子项目，本文档聚焦于 `app/` 主服务。

## 关键能力
- 用户与角色：支持角色/权限动态分配，提供角色与权限 API。
- 策略管理：包含策略创建、更新、订阅与取消订阅。
- 指标查询：基础指标接口示例。
- 系统监控：根路径与 `/health` 返回实时数据库健康状态。

## 安装与启动
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量
   ```bash
   cp env.example .env
   # 根据部署环境调整 MongoDB / JWT / 第三方数据源配置
   ```
3. 初始化基础数据（可选）
   ```bash
   python scripts/init_roles.py
   python scripts/init_admin.py  # 默认账号：admin / admin123
   ```
4. 启动服务
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   或使用提供的 `run.py` / `start.sh` / `start.bat`。

## 运行时功能
- Swagger 文档：`/docs`
- ReDoc 文档：`/redoc`
- OpenAPI JSON：`/openapi.json`
- 健康检查：`/health`

## 默认账号
- 用户名：`admin`
- 密码：`admin123`
- 权限：默认分配 `admin` 角色，请在生产环境及时修改。

## 开发提示
- 所有 MongoDB 操作通过 `DatabaseManager` 统一管理，FastAPI `lifespan` 会自动在启动/退出时建立与关闭连接。
- `app/example/database_usage_examples.py` 演示了最小化的数据库调用方式。
- `python -m compileall app` 可快速检查语法。

## 后续拓展
- 若需要引入其他数据库，可在 `app/db/database.py` 中扩展新的连接逻辑。
- 若要集成更多任务队列或缓存，可参考 `Celery` / `Redis` 相关配置。
