# 股票中台后端实现总结

## 已完成功能

### 1. 用户管理
- 用户注册、登录、认证
- JWT 令牌签发与刷新
- 密码哈希（bcrypt）
- 管理员可执行用户 CRUD

### 2. 角色与权限
- 基于角色的访问控制（RBAC）
- 角色增删改查
- 权限可由角色继承或直接赋给用户
- 常用依赖：
  - `require_roles(["admin"])`
  - `require_permissions(["users:write"])`

### 3. 数据模型
- 用户：`User`、`UserInDB`、`UserCreate`、`UserUpdate`
- 角色：`Role`、`RoleInDB`、`RoleCreate`、`RoleUpdate`
- 策略、指标模型已完成并投入使用

### 4. API 端点
- `/api/v1/auth/*` 认证系列
- `/api/v1/users/*` 用户管理
- `/api/v1/roles/*` 角色管理
- `/api/v1/strategies/*` 策略接口（含权限控制）
- `/api/v1/indicators/*` 指标数据推送与查询

### 5. 权限示例
- 新增策略：`strategies:write`
- 查看策略：`strategies:read`
- 用户/角色管理：管理员权限

## 技术架构

### 数据层
- MongoDB：用户、角色、策略、指标等
- MySQL：股票行情数据（已配置入口）

### 安全机制
- JWT 认证
- 密码哈希存储
- 权限依赖注入
- 请求级别的权限校验

### 核心依赖
- FastAPI
- Pydantic v1
- Motor（异步 MongoDB）
- Python-Jose
- Passlib

## 初始化流程

1. 安装依赖
   ```bash
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
2. 配置环境
   ```bash
   copy env.example .env
   # 编辑 .env，填入数据库连接/JWT 密钥等
   ```
3. 初始化数据
   ```bash
   python scripts/init_roles.py
   python scripts/init_admin.py
   ```
4. 启动服务
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 默认账号
- 管理员：`admin` / `admin123`（首次登录后请修改）
- 默认角色：
  - `admin`：全权限
  - `user`：只读权限

## 常用接口

### 健康检查
```bash
curl http://localhost:8000/health
```

### 新用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'
```

### 登录获取 Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### 访问受保护接口
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/auth/me
```

## 扩展设计

### 权限系统
- 支持细粒度权限拆分
- 权限可复用/继承
- 便于添加新的业务权限点

### 角色系统
- 动态创建、分配
- 可扩展层级或模板

### 用户管理
- 支持多角色、多权限
- 可扩展状态（锁定、禁用等）

## 下一步计划
1. 策略管理
   - 完善 CRUD
   - 支持订阅、推送
2. 权限增强
   - 权限组、继承关系
   - 操作审计日志
3. 数据接入
   - 扩展股票数据源
   - 增加缓存、实时推送
4. 监控与日志
   - API 日志
   - 性能指标
   - 错误追踪

## 注意事项
- 生产环境务必修改默认密码
- 配置正确的数据库连接与索引
- 建议启用 HTTPS 并定期备份
- 持续监控性能与错误日志
