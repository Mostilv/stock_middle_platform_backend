"""
Uvicorn 配置文件
支持开发和生产环境的不同配置
"""

import os
from typing import Optional


class UvicornConfig:
    """Uvicorn 配置类"""
    
    def __init__(self):
        # 基础配置
        self.app = "app.main:app"
        self.host = os.getenv("UVICORN_HOST", "0.0.0.0")
        self.port = int(os.getenv("UVICORN_PORT", "8000"))
        
        # 开发环境配置
        self.reload = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
        self.reload_dirs = ["app", "scripts"]
        self.reload_exclude = ["*.pyc", "*.pyo", "__pycache__", ".git", ".venv"]
        self.reload_delay = 0.25
        
        # 性能配置
        self.workers = int(os.getenv("UVICORN_WORKERS", "1"))
        self.loop = "asyncio"
        self.http = "httptools"
        self.ws = "websockets"
        
        # 日志配置
        self.log_level = os.getenv("UVICORN_LOG_LEVEL", "info")
        self.access_log = os.getenv("UVICORN_ACCESS_LOG", "true").lower() == "true"
        
        # 安全配置
        self.forwarded_allow_ips = "*"
        self.proxy_headers = True
        
        # 超时配置
        self.timeout_keep_alive = 5
        self.timeout_graceful_shutdown = 30
        
        # 开发环境特殊配置
        if self.reload:
            self.workers = 1  # 开发环境只使用单进程
            self.loop = "asyncio"  # 开发环境使用标准 asyncio


def get_uvicorn_config() -> UvicornConfig:
    """获取 Uvicorn 配置"""
    return UvicornConfig()


def get_dev_command() -> str:
    """获取开发环境启动命令"""
    config = get_uvicorn_config()
    return (
        f"uvicorn {config.app} "
        f"--host {config.host} "
        f"--port {config.port} "
        f"--reload "
        f"--reload-dir app "
        f"--reload-dir scripts "
        f"--log-level {config.log_level} "
        f"--access-log"
    )


def get_prod_command() -> str:
    """获取生产环境启动命令"""
    config = get_uvicorn_config()
    return (
        f"uvicorn {config.app} "
        f"--host {config.host} "
        f"--port {config.port} "
        f"--workers {config.workers} "
        f"--loop {config.loop} "
        f"--http {config.http} "
        f"--ws {config.ws} "
        f"--log-level {config.log_level} "
        f"--timeout-keep-alive {config.timeout_keep_alive} "
        f"--timeout-graceful-shutdown {config.timeout_graceful_shutdown}"
    )


if __name__ == "__main__":
    print("=== Uvicorn 配置信息 ===")
    config = get_uvicorn_config()
    print(f"应用: {config.app}")
    print(f"主机: {config.host}")
    print(f"端口: {config.port}")
    print(f"热重载: {config.reload}")
    print(f"工作进程: {config.workers}")
    print(f"日志级别: {config.log_level}")
    print()
    print("=== 开发环境启动命令 ===")
    print(get_dev_command())
    print()
    print("=== 生产环境启动命令 ===")
    print(get_prod_command())
