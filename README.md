# 股票中台后端

`stock_middle_platform_backend` 是股票中台的 FastAPI 后端，负责认证授权、用户管理、股票数据接入、指标查询，以及前端页面需要的账户、设置、涨停复盘、组合和策略订阅等接口。

## 技术栈

- FastAPI
- Uvicorn
- MongoDB + Motor
- Pydantic
- Python-JOSE
- Passlib

## 当前目录结构

```text
.
|-- app/
|   |-- controllers/      路由层
|   |-- core/             安全、依赖注入、数据落库注册
|   |-- db/               数据库连接与 lifespan
|   |-- example/          示例文档与脚本
|   |-- models/           Pydantic 模型
|   |-- repositories/     数据访问层
|   |-- services/         业务服务层
|   |-- utils/            Swagger 与工具函数
|   `-- main.py           FastAPI 入口
|-- scripts/
|-- Dockerfile
|-- docker-compose.yml
|-- README.md
|-- SWAGGER_GUIDE.md
`-- requirements.txt
```

## 主要接口分组

### 认证与权限

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/register`

### 用户与角色

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{id}`
- `PUT /api/v1/users/{id}`
- `DELETE /api/v1/users/{id}`
- `GET /api/v1/roles`

### 股票与指标数据

- `GET /api/v1/stocks/targets`
- `POST /api/v1/stocks/basic`
- `POST /api/v1/stocks/kline`
- `POST /api/v1/indicators/records`
- `GET /api/v1/indicators/records`
- `GET /api/v1/analytics/industry/metrics`
- `POST /api/v1/data/qlib/bars`
- `POST /api/v1/data/market/indices`
- `POST /api/v1/data/limit_up/pool`
- `POST /api/v1/integrity/check`

### 前端页面相关接口

- `GET /api/v1/account/profile`
- `PUT /api/v1/account/profile`
- `POST /api/v1/account/password`
- `GET /api/v1/settings/data`
- `POST /api/v1/settings/data`
- `GET /api/v1/market/data`
- `GET /api/v1/limitup/overview`
- `GET /api/v1/portfolio/overview`
- `POST /api/v1/portfolio/strategies/{strategy_id}/toggle`
- `GET /api/v1/strategies/subscriptions`
- `POST /api/v1/strategies/subscriptions`
- `POST /api/v1/strategies/subscriptions/blacklist`

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

### 2. 准备环境变量

如果仓库内提供了 `env.example`，复制为 `.env` 并补齐 MongoDB、JWT 等配置；如果没有，请直接按 `app/config.py` 中读取的字段自行创建。

### 3. 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 文档与调试

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`
- 健康检查: `http://localhost:8000/health`

更详细的说明见 `SWAGGER_GUIDE.md`。

## 当前实现说明

- 后端目录名义上采用 `controllers -> services -> repositories` 分层
- 部分前端页面接口目前集中在 `app/services/frontend_state_service.py`
- `data_feed` 中的部分写库逻辑仍直接在控制器层完成

以上结构能工作，但还处于持续整理阶段。后续如果进行架构重构，应优先按领域拆分服务并统一数据落库路径。
