#!/usr/bin/env python3
"""
项目启动脚本
支持开发和生产环境的不同启动方式
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import subprocess
import argparse
from pathlib import Path


def run_dev_server():
    """启动开发环境服务器"""
    print("启动开发环境服务器...")
    print("监控目录: app/, scripts/")
    print("热重载: 已启用")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
        "--reload-dir",
        "app",
        "--reload-dir",
        "scripts",
        "--log-level",
        "info",
        "--access-log",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


def run_prod_server():
    """启动生产环境服务器"""
    print("🚀 启动生产环境服务器...")
    print("⚡ 多进程模式")
    print("🌐 访问地址: http://localhost:8000")
    print()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--workers",
        "4",
        "--loop",
        "asyncio",
        "--http",
        "httptools",
        "--ws",
        "websockets",
        "--log-level",
        "info",
        "--timeout-keep-alive",
        "5",
        "--timeout-graceful-shutdown",
        "30",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


def run_with_gunicorn():
    """使用 Gunicorn 启动服务器"""
    print("🚀 使用 Gunicorn 启动服务器...")
    print("⚡ 企业级部署模式")
    print("🌐 访问地址: http://localhost:8000")
    print()

    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "app.main:app",
        "-w",
        "4",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "--bind",
        "0.0.0.0:8000",
        "--timeout",
        "120",
        "--keep-alive",
        "5",
        "--max-requests",
        "1000",
        "--max-requests-jitter",
        "100",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请先安装 gunicorn: pip install gunicorn")
        sys.exit(1)


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import uvicorn

        print("Uvicorn 已安装")
    except ImportError:
        print("Uvicorn 未安装，请运行: pip install uvicorn[standard]")
        sys.exit(1)

    try:
        import fastapi

        print("FastAPI 已安装")
    except ImportError:
        print("FastAPI 未安装，请运行: pip install fastapi")
        sys.exit(1)


def show_config():
    """显示当前配置"""
    print("📋 当前 Uvicorn 配置:")
    print(f"   应用模块: app.main:app")
    print(f"   主机地址: 0.0.0.0")
    print(f"   端口: 8000")
    print(f"   热重载: 开发环境启用")
    print(f"   工作进程: 开发环境1个，生产环境4个")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="股票中间平台后端启动脚本")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "gunicorn"],
        default="dev",
        help="启动模式: dev(开发), prod(生产), gunicorn(企业级)",
    )
    parser.add_argument("--config", action="store_true", help="显示配置信息")

    args = parser.parse_args()

    # 显示欢迎信息
    print("股票中间平台后端")
    print("=" * 50)

    # 检查依赖
    check_dependencies()

    # 显示配置
    if args.config:
        show_config()

    # 根据模式启动
    if args.mode == "dev":
        run_dev_server()
    elif args.mode == "prod":
        run_prod_server()
    elif args.mode == "gunicorn":
        run_with_gunicorn()
    else:
        print(f"❌ 未知的启动模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
