"""
Swagger配置文件
提供Swagger UI的自定义配置和工具函数
"""

from typing import Dict, Any
from fastapi.openapi.utils import get_openapi
from app.config import settings

# Swagger UI 自定义配置
SWAGGER_UI_CONFIG = {
    "defaultModelsExpandDepth": -1,  # 隐藏模型部分
    "defaultModelExpandDepth": 3,    # 模型展开深度
    "docExpansion": "list",          # 默认展开方式: none, list, full
    "filter": True,                  # 启用搜索过滤
    "showExtensions": True,          # 显示扩展信息
    "showCommonExtensions": True,    # 显示通用扩展
    "syntaxHighlight.theme": "monokai",  # 代码高亮主题
    "tryItOutEnabled": True,         # 启用"Try it out"功能
    "requestInterceptor": "function(request) { console.log('Request:', request); return request; }",
    "responseInterceptor": "function(response) { console.log('Response:', response); return response; }",
    "persistAuthorization": True,    # 保持授权状态
    "displayRequestDuration": True,  # 显示请求耗时
    "displayOperationId": False,     # 隐藏操作ID
    "showMutatedRequest": True,      # 显示修改后的请求
    "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],  # 支持的HTTP方法
}

# API标签配置
API_TAGS = [
    {
        "name": "认证",
        "description": "用户认证和授权相关接口，包括注册、登录、JWT验证等",
        "externalDocs": {
            "description": "认证流程说明",
            "url": "https://docs.stockplatform.com/auth"
        }
    },
    {
        "name": "用户管理",
        "description": "用户信息管理、角色权限分配、用户状态管理等",
        "externalDocs": {
            "description": "用户管理指南",
            "url": "https://docs.stockplatform.com/users"
        }
    },
    {
        "name": "策略管理",
        "description": "量化策略的创建、编辑、删除、回测和优化等",
        "externalDocs": {
            "description": "策略开发指南",
            "url": "https://docs.stockplatform.com/strategies"
        }
    },
    {
        "name": "技术指标",
        "description": "股票技术指标计算、分析和可视化等",
        "externalDocs": {
            "description": "技术指标说明",
            "url": "https://docs.stockplatform.com/indicators"
        }
    },
    {
        "name": "系统监控",
        "description": "系统健康检查、性能监控、日志查看等",
        "externalDocs": {
            "description": "系统监控指南",
            "url": "https://docs.stockplatform.com/monitoring"
        }
    }
]

# 安全配置
SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer Token认证，在登录后获取token，在请求头中添加: Authorization: Bearer {token}"
    }
}

# 服务器配置
SERVERS = [
    {
        "url": "http://localhost:8000",
        "description": "开发环境 - 本地开发服务器"
    },
    {
        "url": "http://localhost:8080",
        "description": "开发环境 - 备用端口"
    },
    {
        "url": "https://api.stockplatform.com",
        "description": "生产环境 - 正式API服务器"
    },
    {
        "url": "https://staging-api.stockplatform.com",
        "description": "测试环境 - 预发布服务器"
    }
]

def get_custom_openapi(app, title: str, version: str, description: str) -> Dict[str, Any]:
    """
    生成自定义的OpenAPI规范
    
    Args:
        app: FastAPI应用实例
        title: API标题
        version: API版本
        description: API描述
    
    Returns:
        自定义的OpenAPI规范字典
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
    )
    
    # 添加安全配置
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES
    
    # 设置全局安全要求
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # 添加标签信息
    openapi_schema["tags"] = API_TAGS
    
    # 添加服务器信息
    openapi_schema["servers"] = SERVERS
    
    # 添加外部文档链接
    openapi_schema["externalDocs"] = {
        "description": "更多文档",
        "url": "https://docs.stockplatform.com"
    }
    
    # 添加信息扩展
    openapi_schema["info"]["x-logo"] = {
        "url": "https://via.placeholder.com/200x200/0066cc/ffffff?text=SP",
        "altText": "股票中间平台Logo"
    }
    
    # 添加标签扩展
    openapi_schema["info"]["x-tagGroups"] = [
        {
            "name": "核心功能",
            "tags": ["认证", "用户管理"]
        },
        {
            "name": "业务功能",
            "tags": ["策略管理", "技术指标"]
        },
        {
            "name": "系统功能",
            "tags": ["系统监控"]
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def get_swagger_ui_parameters() -> Dict[str, Any]:
    """
    获取Swagger UI参数配置
    
    Returns:
        Swagger UI参数字典
    """
    return SWAGGER_UI_CONFIG.copy()

def get_api_tags() -> list:
    """
    获取API标签配置
    
    Returns:
        API标签列表
    """
    return API_TAGS.copy()

def get_security_schemes() -> Dict[str, Any]:
    """
    获取安全配置
    
    Returns:
        安全配置字典
    """
    return SECURITY_SCHEMES.copy()

def get_servers() -> list:
    """
    获取服务器配置
    
    Returns:
        服务器配置列表
    """
    return SERVERS.copy()


