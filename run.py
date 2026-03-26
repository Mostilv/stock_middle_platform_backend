#!/usr/bin/env python3
"""Backend launcher for development and production."""

import argparse
import subprocess
import sys


def run_dev_server() -> None:
    print("Starting backend in development mode")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
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
        "--log-level",
        "info",
        "--access-log",
    ]
    subprocess.run(cmd, check=True)


def run_prod_server() -> None:
    print("Starting backend in production mode")
    print("URL: http://localhost:8000")
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
    subprocess.run(cmd, check=True)


def run_with_gunicorn() -> None:
    print("Starting backend with gunicorn")
    print("URL: http://localhost:8000")
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
    subprocess.run(cmd, check=True)


def check_dependencies() -> None:
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        print("Install backend requirements first.")
        sys.exit(1)


def show_config() -> None:
    print("Backend launch configuration")
    print("  module: app.main:app")
    print("  host: 0.0.0.0")
    print("  port: 8000")
    print("  dev workers: 1")
    print("  prod workers: 4")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock platform backend launcher")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "gunicorn"],
        default="dev",
        help="Launch mode",
    )
    parser.add_argument("--config", action="store_true", help="Show config")
    args = parser.parse_args()

    check_dependencies()

    if args.config:
        show_config()

    try:
        if args.mode == "dev":
            run_dev_server()
        elif args.mode == "prod":
            run_prod_server()
        else:
            run_with_gunicorn()
    except KeyboardInterrupt:
        print("\nBackend stopped")
    except subprocess.CalledProcessError as exc:
        print(f"Backend start failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
