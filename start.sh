#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 股票中间平台后端${NC}"
echo "========================================"

echo
echo -e "${YELLOW}📋 选择启动模式:${NC}"
echo "1. 开发环境 (热重载)"
echo "2. 生产环境 (多进程)"
echo "3. 企业级 (Gunicorn)"
echo "4. 显示配置信息"
echo

read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo
        echo -e "${GREEN}🚀 启动开发环境服务器...${NC}"
        echo "📁 监控目录: app/, scripts/"
        echo "🔄 热重载: 已启用"
        echo "🌐 访问地址: http://localhost:8000"
        echo "📚 API文档: http://localhost:8000/docs"
        echo
        python3 run.py --mode dev
        ;;
    2)
        echo
        echo -e "${GREEN}🚀 启动生产环境服务器...${NC}"
        echo "⚡ 多进程模式"
        echo "🌐 访问地址: http://localhost:8000"
        echo
        python3 run.py --mode prod
        ;;
    3)
        echo
        echo -e "${GREEN}🚀 使用 Gunicorn 启动服务器...${NC}"
        echo "⚡ 企业级部署模式"
        echo "🌐 访问地址: http://localhost:8000"
        echo
        python3 run.py --mode gunicorn
        ;;
    4)
        echo
        python3 run.py --config
        read -p "按回车键继续..."
        ;;
    *)
        echo -e "${RED}❌ 无效选择，请重新运行脚本${NC}"
        read -p "按回车键继续..."
        ;;
esac
