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
|   |   |-- indicators.py
|   |   |-- roles.py
|   |   |-- strategies.py
|   |   |-- users.py
|   |   +-- __init__.py
|   |-- services
|   |   |-- indicator_service.py
|   |   |-- role_service.py
|   |   |-- strategy_service.py
|   |   |-- user_service.py
|   |   +-- __init__.py
|   |-- repositories
|   |   |-- base.py
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

## Default Account
- Username: `admin`
- Password: `admin123`
- Permissions: granted through the `admin` role; adjust after first login if needed.
