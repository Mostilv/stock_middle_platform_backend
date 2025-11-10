# Stock Middle Platform Backend

## Overview
- FastAPI based backend that powers the stock middle platform (user management, roles, indicators, strategies).
- MongoDB is used as the primary datastore through the async Motor driver.
- JWT authentication is enabled by default together with role/permission validation and automatically configured Swagger docs.

## Tech Stack
- FastAPI + Uvicorn
- MongoDB (Motor async driver)
- Optional: Redis / Celery for background processing
- Python-JOSE + Passlib for JWT handling

## Layered Architecture
The backend now follows a three-layer design without nested projects:
- `app/controllers`: request/response handling (FastAPI routers).
- `app/services`: business logic and orchestration.
- `app/repositories`: data access helpers talking to MongoDB.

Shared configuration, domain models, and utilities remain under `app/config`, `app/models`, and `app/utils`.

## Project Layout
```
|-- app
|   |-- controllers
|   |   |-- auth.py
|   |   |-- data_feed.py
|   |   |-- indicators.py
|   |   |-- roles.py
|   |   |-- strategies.py
|   |   |-- users.py
|   |   +-- __init__.py
|   |-- services
|   |   |-- indicator_service.py
|   |   |-- qlib_data_service.py
|   |   |-- role_service.py
|   |   |-- strategy_service.py
|   |   |-- user_service.py
|   |   +-- __init__.py
|   |-- repositories
|   |   |-- base.py
|   |   |-- indicator_repository.py
|   |   |-- qlib_data_repository.py
|   |   |-- role_repository.py
|   |   |-- strategy_repository.py
|   |   |-- user_repository.py
|   |   +-- __init__.py
|   |-- config.py
|   |-- core
|   |-- db
|   |-- example
|   |-- main.py
|   |-- models
|   |   |-- indicator.py
|   +-- utils
|-- scripts
|-- env.example
|-- requirements.txt
|-- docker-compose.yml / Dockerfile
|-- run.py / start.{bat,sh}
|-- SWAGGER_GUIDE.md / SWAGGER_INTEGRATION_SUMMARY.md
|-- test_api.py / test_swagger*.py
|-- uvicorn_config.py
```

Legacy assets formerly kept inside `stock-system/` have been removed to avoid nested projects.

## Getting Started
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables
   ```bash
   cp env.example .env
   # Adjust MongoDB / JWT / data source configuration as needed
   ```
3. (Optional) Seed initial data
   ```bash
   python scripts/init_roles.py
   python scripts/init_admin.py  # default admin/admin123
   ```
4. Run the service
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Helper scripts (`run.py`, `start.sh`, `start.bat`) are also available.

## Useful Endpoints
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
- Health check: `/health`
- Qlib data ingest: `POST /api/v1/data/qlib/bars`（需 Bearer Token）
- Indicator ingest: `POST /api/v1/indicators/records`（需 `indicators:write` 权限）
- Indicator query: `GET /api/v1/indicators/records`（需 `indicators:read` 权限）

## Qlib 数据接入接口
The `/api/v1/data/qlib/bars` endpoint accepts the same column names used by [Microsoft Qlib](https://github.com/microsoft/qlib) for stock data. Payloads must include a Bearer token (JWT) issued by this service.

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/data/qlib/bars \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "provider": "partner-feed",
        "market": "cn",
        "timezone": "Asia/Shanghai",
        "records": [
          {
            "instrument": "SH600519",
            "datetime": "2024-10-08T15:00:00+08:00",
            "freq": "1d",
            "open": 1600.5,
            "high": 1611.2,
            "low": 1590.0,
            "close": 1605.4,
            "volume": 123456,
            "amount": 987654321,
            "factor": 1.0,
            "turnover": 0.35,
            "limit_status": "none",
            "suspended": false,
            "extra_fields": {
              "Ref(close,1)": 1588.1
            }
          }
        ]
      }'
```

The API normalizes instruments to uppercase, converts timestamps to UTC before persistence, and upserts on the `(instrument, freq, datetime)` compound key so repeated submissions remain idempotent.

## 指标数据推送与查询
指标计算已经外部化，本项目负责接收指标结果并提供统一查询。

- 推送接口：`POST /api/v1/indicators/records`
  - 权限要求：`indicators:write`
  - 支持批量写入，同一 `(indicator, symbol, timeframe, timestamp)` 会覆盖
  - `value`、`values`、`payload` 至少提供其一
- 查询接口：`GET /api/v1/indicators/records`
  - 权限要求：`indicators:read`
  - 支持按指标、股票、时间范围、标签过滤
  - 返回 `data + total` 结构，方便前端分页

示例推送：

```bash
curl -X POST http://localhost:8000/api/v1/indicators/records \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "provider": "quant-service",
        "records": [
          {
            "symbol": "SH600519",
            "indicator": "rsi14",
            "timeframe": "1d",
            "timestamp": "2024-10-08T15:00:00+08:00",
            "value": 56.17,
            "values": {"overbought": 70, "oversold": 30},
            "payload": {"window": 14},
            "tags": ["daily", "demo"]
          }
        ]
      }'
```

示例查询：

```bash
curl -G http://localhost:8000/api/v1/indicators/records \
  -H "Authorization: Bearer <token>" \
  --data-urlencode "indicator=rsi14" \
  --data-urlencode "symbol=SH600519" \
  --data-urlencode "timeframe=1d" \
  --data-urlencode "limit=50"
```

## Default Account
- Username: `admin`
- Password: `admin123`
- Permissions: granted through the `admin` role; adjust after first login if needed.
