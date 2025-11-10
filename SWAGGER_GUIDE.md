# 🚀 Swagger API 文档使用指南

## 📖 概述

本项目使用 **FastAPI + Swagger UI** 提供专业的API文档和测试界面。Swagger是目前最主流的API文档工具，具有以下优势：

- ✅ **自动生成文档** - 基于代码注释自动生成
- ✅ **交互式测试** - 可直接在界面上测试API
- ✅ **实时更新** - 代码修改后文档自动更新
- ✅ **多格式支持** - 支持OpenAPI 3.0规范
- ✅ **团队协作** - 前后端开发人员可以更好地协作

## 🌐 访问地址

启动项目后，可以通过以下地址访问：

| 文档类型 | 地址 | 说明 |
|---------|------|------|
| **Swagger UI** | `http://localhost:8000/docs` | 主要文档界面，支持交互式测试 |
| **ReDoc** | `http://localhost:8000/redoc` | 更美观的文档展示界面 |
| **OpenAPI JSON** | `http://localhost:8000/openapi.json` | 原始OpenAPI规范文件 |

## 🎯 主要功能

### 1. 认证与授权
- 用户注册、登录
- JWT Token认证
- 基于角色的权限控制

### 2. 用户管理
- 用户信息管理
- 角色权限分配
- 用户状态管理

### 3. 策略管理
- 量化策略创建和管理
- 策略回测和优化
- 投资组合管理

### 4. 指标数据
- 外部指标写入接口（POST `/api/v1/indicators/records`）
- MongoDB 持久化与查询（GET `/api/v1/indicators/records`）
- 标签筛选、时间范围、权限控制

### 5. 系统监控
- 健康检查
- 性能监控
- 日志查看

## 🔐 认证说明

### JWT Token使用
1. 首先调用 `/api/v1/auth/login` 接口获取token
2. 在Swagger UI右上角点击 "Authorize" 按钮
3. 输入格式：`Bearer {your_token}`
4. 点击 "Authorize" 确认

### 请求头示例
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🛠️ 自定义配置

### Swagger UI参数
项目支持自定义Swagger UI的显示参数，配置文件：`app/utils/swagger_config.py`

```python
SWAGGER_UI_CONFIG = {
    "defaultModelsExpandDepth": -1,  # 隐藏模型部分
    "docExpansion": "list",          # 默认展开方式
    "filter": True,                  # 启用搜索过滤
    "tryItOutEnabled": True,         # 启用"Try it out"功能
    # ... 更多配置
}
```

### API标签分组
API接口按功能分组，便于查找和管理：

- **核心功能**: 认证、用户管理
- **业务功能**: 策略管理、技术指标  
- **系统功能**: 系统监控

## 📝 开发规范

### 1. 接口文档注释
```python
@router.post("/users", response_model=User, tags=["用户管理"])
async def create_user(user: UserCreate):
    """
    创建新用户
    
    - **username**: 用户名，必须唯一
    - **email**: 邮箱地址，必须有效
    - **password**: 密码，至少8位字符
    
    返回新创建的用户信息
    """
    pass
```

### 2. 响应模型定义
```python
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00"
            }
        }
```

### 3. 错误响应
```python
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    获取用户信息
    
    如果用户不存在，返回404错误
    """
    if not user_exists(user_id):
        raise HTTPException(
            status_code=404,
            detail="用户不存在"
        )
```

## 🔧 高级功能

### 1. 请求/响应拦截器
Swagger UI支持自定义请求和响应拦截器，便于调试：

```javascript
// 在Swagger UI中可以看到请求和响应的日志
requestInterceptor: "function(request) { console.log('Request:', request); return request; }",
responseInterceptor: "function(response) { console.log('Response:', response); return response; }"
```

### 2. 持久化授权
启用 `persistAuthorization: true` 后，认证状态会在页面刷新后保持。

### 3. 代码高亮
使用Monokai主题提供更好的代码可读性。

## 🚀 快速开始

### 1. 启动项目
```bash
# 使用uvicorn启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用项目脚本
python run.py
```

### 2. 访问文档
打开浏览器访问：`http://localhost:8000/docs`

### 3. 测试接口
1. 展开需要测试的接口
2. 点击 "Try it out" 按钮
3. 填写参数
4. 点击 "Execute" 执行

## 📚 相关资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [OpenAPI规范](https://swagger.io/specification/)
- [Swagger UI文档](https://swagger.io/tools/swagger-ui/)
- [ReDoc文档](https://redocly.github.io/redoc/)

## 🤝 贡献指南

如果您想改进API文档：

1. 完善接口注释
2. 添加示例数据
3. 优化错误响应
4. 更新配置参数

## 📞 技术支持

如有问题，请联系开发团队：
- 邮箱：dev@stockplatform.com
- 项目地址：https://github.com/stockplatform/backend

---

**🎉 享受使用Swagger带来的开发体验提升！**


