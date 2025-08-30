# 股票中间平台后端

## 项目简介
基于Python + FastAPI + MongoDB + MySQL的股票中间平台后端系统，支持用户管理、策略订阅和指标展示。

## 技术栈
- **Web框架**: FastAPI
- **数据库**: MongoDB (用户数据、策略数据) + MySQL (股票数据)
- **数据源**: baostock、akshare
- **认证**: JWT
- **任务队列**: Celery + Redis

## 项目结构
```
stock_middle_platform_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置文件
│   ├── database.py             # 数据库连接
│   ├── models/                 # 数据模型
│   ├── schemas/                # Pydantic模型
│   ├── api/                    # API路由
│   ├── core/                   # 核心功能
│   ├── services/               # 业务逻辑
│   └── utils/                  # 工具函数
├── alembic/                    # 数据库迁移
├── requirements.txt            # 依赖包
└── .env                        # 环境变量
```

## 功能特性
- 用户管理（注册、登录、权限控制）
- 策略管理（用户策略、管理员策略）
- 指标展示（无需权限）
- 数据源集成（baostock、akshare）

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件配置数据库连接等信息
```

3. 启动服务
```bash
uvicorn app.main:app --reload
```

## API文档
启动服务后访问: http://localhost:8000/docs
