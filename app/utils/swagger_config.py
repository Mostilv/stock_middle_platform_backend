"""Utility helpers for FastAPI OpenAPI and Swagger configuration."""

from typing import Any, Dict, List

from fastapi.openapi.utils import get_openapi

SWAGGER_UI_CONFIG: Dict[str, Any] = {
    "defaultModelsExpandDepth": -1,
    "docExpansion": "none",
    "persistAuthorization": True,
    "displayRequestDuration": True,
}

API_TAGS: List[Dict[str, str]] = [
    {"name": "auth", "description": "Authentication and token endpoints."},
    {"name": "users", "description": "User, role and permission management."},
    {"name": "strategies", "description": "Strategy management and subscriptions."},
    {"name": "indicators", "description": "Indicator calculation and queries."},
    {"name": "stocks", "description": "Raw stock basic and kline queries."},
    {"name": "data", "description": "Data ingestion endpoints."},
    {"name": "integrity", "description": "Stored market data integrity checks."},
    {"name": "analytics", "description": "Industry and derived analytics."},
    {"name": "account", "description": "Account and system settings."},
    {"name": "market", "description": "Market snapshot endpoints."},
    {"name": "limitup", "description": "Limit-up monitoring endpoints."},
    {"name": "portfolio", "description": "Portfolio endpoints."},
    {"name": "system", "description": "Service status and health endpoints."},
]

SECURITY_SCHEMES: Dict[str, Any] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Send `Authorization: Bearer <token>`.",
    }
}

SERVERS: List[Dict[str, str]] = [
    {"url": "http://localhost:8000", "description": "Local development"},
]


def get_custom_openapi(
    app: Any,
    title: str,
    version: str,
    description: str,
) -> Dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES
    openapi_schema["tags"] = API_TAGS
    openapi_schema["servers"] = SERVERS
    return openapi_schema


def get_swagger_ui_parameters() -> Dict[str, Any]:
    return SWAGGER_UI_CONFIG.copy()


def get_api_tags() -> List[Dict[str, str]]:
    return API_TAGS.copy()


def get_servers() -> List[Dict[str, str]]:
    return SERVERS.copy()
