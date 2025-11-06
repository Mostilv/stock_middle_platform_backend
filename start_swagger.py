#!/usr/bin/env python3
"""
启动脚本 - 测试Swagger功能
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 启动股票中间平台后端服务...")
    print("📚 Swagger文档地址: http://localhost:8000/docs")
    print("📖 ReDoc文档地址: http://localhost:8000/redoc")
    print("🔧 OpenAPI JSON: http://localhost:8000/openapi.json")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info",
    )
