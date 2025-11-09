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
- Qlib data ingest: `POST /api/v1/data/qlib/bars` (requires Bearer token)

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

## Default Account
- Username: `admin`
- Password: `admin123`
- Permissions: granted through the `admin` role; adjust after first login if needed.
