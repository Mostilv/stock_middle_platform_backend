"""
Utility helpers for FastAPI's OpenAPI/Swagger configuration.
"""

from typing import Any, Dict, List

from fastapi.openapi.utils import get_openapi

# Keep the UI configuration compact and readable.
SWAGGER_UI_CONFIG: Dict[str, Any] = {
    "defaultModelsExpandDepth": -1,
    "docExpansion": "none",
    "persistAuthorization": True,
    "displayRequestDuration": True,
}

API_TAGS: List[Dict[str, str]] = [
    {"name": "认证", "description": "登录与令牌管理"},
    {"name": "用户管理", "description": "用户、角色与权限接口"},
    {"name": "策略管理", "description": "量化策略维护与订阅"},
    {"name": "技术指标", "description": "常用指标查询"},
    {"name": "系统监控", "description": "服务状态与健康检查"},
]

SECURITY_SCHEMES: Dict[str, Any] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "在 Authorization 请求头中携带 Bearer {token}。",
    }
}

SERVERS: List[Dict[str, str]] = [
    {"url": "http://localhost:8000", "description": "本地开发环境"},
]


def get_custom_openapi(app, title: str, version: str, description: str) -> Dict[str, Any]:
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
