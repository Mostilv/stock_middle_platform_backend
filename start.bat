@echo off
chcp 65001 >nul
echo 🎯 股票中间平台后端
echo ========================================

echo.
echo 📋 选择启动模式:
echo 1. 开发环境 (热重载)
echo 2. 生产环境 (多进程)
echo 3. 企业级 (Gunicorn)
echo 4. 显示配置信息
echo.

set /p choice=请输入选择 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 🚀 启动开发环境服务器...
    echo 📁 监控目录: app/, scripts/
    echo 🔄 热重载: 已启用
    echo 🌐 访问地址: http://localhost:8000
    echo 📚 API文档: http://localhost:8000/docs
    echo.
    python run.py --mode dev
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动生产环境服务器...
    echo ⚡ 多进程模式
    echo 🌐 访问地址: http://localhost:8000
    echo.
    python run.py --mode prod
) else if "%choice%"=="3" (
    echo.
    echo 🚀 使用 Gunicorn 启动服务器...
    echo ⚡ 企业级部署模式
    echo 🌐 访问地址: http://localhost:8000
    echo.
    python run.py --mode gunicorn
) else if "%choice%"=="4" (
    echo.
    python run.py --config
    pause
) else (
    echo ❌ 无效选择，请重新运行脚本
    pause
)
