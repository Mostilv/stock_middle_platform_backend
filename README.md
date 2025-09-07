# 股票中间平台后端

## 项目简介
基于Python + FastAPI + MySQL + MongoDB的股票中间平台后端系统，支持用户管理、策略订阅、指标展示和聚宽调仓仓位管理。

## 技术栈
- **Web框架**: FastAPI
- **ASGI服务器**: Uvicorn (官方推荐)
- **数据库**: MySQL (用户数据、角色权限) + MongoDB (股票数据、调仓记录)
- **数据源**: baostock、akshare
- **认证**: JWT
- **任务队列**: Celery + Redis

## 数据存储架构

### MySQL - 用户相关数据
- 用户账户信息
- 角色权限管理
- 用户配置和偏好
- 登录日志等

**优势：**
- ACID事务支持，数据一致性更好
- 复杂查询性能优秀（JOIN、权限检查等）
- 成熟的关系型数据库，运维经验丰富

### MongoDB - 业务数据
- 股票实时行情数据
- 历史K线数据
- 聚宽调仓仓位记录
- 策略执行日志
- 持仓快照等

**优势：**
- 适合时序数据存储
- 灵活的数据结构，便于扩展
- 高写入性能
- 支持复杂嵌套数据

## 项目结构
```
stock_middle_platform_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置文件
│   ├── database.py             # 数据库连接
│   ├── models/                 # 数据模型
│   │   ├── user.py            # MySQL用户模型
│   │   ├── role.py            # MySQL角色权限模型
│   │   ├── portfolio.py       # MongoDB调仓仓位模型
│   │   ├── strategy.py        # 策略模型
│   │   └── indicators.py      # 指标模型
│   ├── api/                    # API路由
│   ├── core/                   # 核心功能
│   ├── services/               # 业务逻辑
│   └── utils/                  # 工具函数
├── scripts/                     # 初始化脚本
├── uvicorn_config.py           # Uvicorn 配置
├── run.py                      # 启动脚本
├── start.bat                   # Windows 启动脚本
├── start.sh                    # Linux/Mac 启动脚本
├── Dockerfile                  # Docker 配置
├── docker-compose.yml          # Docker Compose 配置
├── requirements.txt             # 依赖包
└── .env                        # 环境变量
```

## 功能特性
- 用户管理（注册、登录、权限控制）
- 角色权限管理（RBAC）
- 策略管理（用户策略、管理员策略）
- 指标展示（无需权限）
- 聚宽调仓仓位管理
- 数据源集成（baostock、akshare）

### 权限模型
- 用户可直接拥有 `permissions`，并可被分配多个 `roles`。
- 角色 `roles` 定义一组 `permissions`，请求时会合并用户直接权限与其角色权限。

内置依赖：
- `require_roles(["admin"])`：要求用户具备指定角色。
- `require_permissions(["users:write"])`：要求用户具备指定权限（含来自角色的权限）。

## 🚀 启动方式

### 方式一：使用启动脚本（推荐）

#### Windows 用户
```bash
# 双击运行或命令行执行
start.bat

# 或直接运行 Python 脚本
python run.py --mode dev
```

#### Linux/Mac 用户
```bash
# 添加执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh

# 或直接运行 Python 脚本
python3 run.py --mode dev
```

### 方式二：直接使用 Uvicorn

#### 开发环境（热重载）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产环境（多进程）
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 企业级部署（Gunicorn + Uvicorn）
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 方式三：Docker 部署

#### 使用 Docker Compose（推荐）
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

#### 单独构建应用
```bash
# 构建镜像
docker build -t stock-platform .

# 运行容器
docker run -p 8000:8000 stock-platform
```

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

3. 初始化数据库
```bash
# 创建MySQL表结构
python scripts/create_tables.py

# 初始化默认角色与权限
python scripts/init_roles.py

# 初始化超级管理员（用户名: admin, 密码: admin123，请尽快修改）
python scripts/init_admin.py
```

4. 启动服务
```bash
# 使用启动脚本（推荐）
./start.sh  # Linux/Mac
start.bat   # Windows

# 或直接运行
python run.py --mode dev
```

## Uvicorn 配置说明

### 开发环境配置
- **热重载**: 启用，监控 `app/` 和 `scripts/` 目录
- **工作进程**: 1个（单进程便于调试）
- **日志级别**: info
- **访问日志**: 启用

### 生产环境配置
- **热重载**: 禁用
- **工作进程**: 4个（多进程提升性能）
- **HTTP引擎**: httptools（高性能）
- **WebSocket引擎**: websockets
- **超时配置**: 连接保持5秒，优雅关闭30秒

### 企业级配置
- **进程管理**: Gunicorn
- **工作进程**: 4个 Uvicorn Worker
- **负载均衡**: 自动进程间负载均衡
- **健康检查**: 内置健康检查端点

## 数据库配置

### MySQL配置
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DB=stock_platform
```

### MongoDB配置
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=stock_platform
```

## 聚宽调仓仓位管理

### 数据模型特点
- **调仓记录**：记录每次调仓的前后持仓变化
- **持仓快照**：每日持仓状态快照
- **风控指标**：调仓时的风控参数
- **操作日志**：详细的买卖订单记录

### 存储优势
- **灵活结构**：支持复杂的嵌套数据（持仓明细、风控指标等）
- **时序优化**：按时间索引，查询性能优秀
- **扩展性强**：易于添加新的字段和功能

## API文档
启动服务后访问: http://localhost:8000/docs

## 默认账户

- **管理员账户**
  - 用户名: `admin`
  - 密码: `admin123`
  - 权限: 所有权限

- **默认角色**
  - `admin`: 系统管理员，拥有所有权限
  - `user`: 普通用户，拥有读取权限

## 性能优化

### Uvicorn 性能调优
- **工作进程数**: 建议设置为 CPU 核心数的 2-4 倍
- **HTTP引擎**: 使用 `httptools` 获得最佳性能
- **循环引擎**: 生产环境可使用 `uvloop`（仅限 Linux）
- **连接池**: 配置适当的连接池大小

### 数据库优化
- **MySQL**: 配置适当的连接池和查询缓存
- **MongoDB**: 创建合适的索引，使用连接池
- **Redis**: 配置持久化和内存策略

## 监控与日志

### 健康检查
- 端点: `/health`
- 检查项目: 数据库连接、服务状态
- 监控频率: 30秒

### 日志配置
- **开发环境**: 详细日志，包含访问日志
- **生产环境**: 关键日志，错误追踪
- **日志格式**: 结构化JSON格式

## 注意事项

- 生产环境中请修改默认密码
- 请配置适当的数据库连接信息
- 建议启用HTTPS
- 定期备份数据库
- 监控服务性能和错误日志
- MySQL和MongoDB都需要单独配置和维护
- 生产环境建议使用 Docker 或容器化部署
- 定期更新依赖包版本
