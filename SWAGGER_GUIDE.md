# 🚀 Swagger API 文档使用指南

## 📖 概述
后端通过 **FastAPI + Swagger UI** 提供完整的 API 文档与一键测试能力，具备以下优势：
- ✅ 自动生成：基于路由声明与 Pydantic 模型实时产出文档
- ✅ 交互测试：直接在页面点击 “Try it out” 发起请求
- ✅ 实时更新：代码改动立刻反馈到文档
- ✅ OpenAPI 3.0：兼容多语言、多工具链
- ✅ 协作友好：前后端共享统一接口描述

## 🌐 访问入口

| 文档类型 | 地址 | 说明 |
| --- | --- | --- |
| Swagger UI | `http://localhost:8000/docs` | 默认交互式文档 |
| ReDoc | `http://localhost:8000/redoc` | 更易阅读的长文档展示 |
| OpenAPI JSON | `http://localhost:8000/openapi.json` | 规范原始文件，可供代码生成 |

## 🎯 主要能力
### 认证与授权
- 用户注册、登录
- JWT Bearer 认证
- 角色/权限校验

### 用户/角色管理
- 用户 CRUD、状态控制
- 角色与权限分配

### 策略与指标
- 策略 CRUD、信号维护
- 指标入库与检索（`/api/v1/indicators/records`）

### 系统监控
- `/health` 健康检查
- `/docs` 可视化调试

## 🔐 JWT 使用说明
1. 先调用 `/api/v1/auth/login` 获取 access token。
2. 在 Swagger UI 右上角点击 `Authorize`。
3. 以 `Bearer <token>` 格式填写。
4. 认证成功后即可调试需要权限的接口。

示例请求头：
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🛠️ 自定义配置
配置位于 `app/utils/swagger_config.py`，常用项：

```python
SWAGGER_UI_CONFIG = {
    "docExpansion": "list",          # 控制折叠/展开
    "defaultModelsExpandDepth": -1,  # 默认隐藏 Schemas
    "filter": True,                  # 启用搜索过滤
    "tryItOutEnabled": True,         # 默认打开 Try it out
    "persistAuthorization": True,    # 刷新后保留授权
}
```

接口标签统一按模块划分：核心（认证/用户）、业务（策略/指标）、系统（监控/工具）。

## 📝 注释规范
### 路由示例
```python
@router.post("/users", response_model=User, tags=["用户管理"])
async def create_user(user: UserCreate):
    """
    创建新用户

    - **username**: 唯一用户名
    - **email**: 有效邮箱
    - **password**: 至少 8 位
    """
```

### 响应模型
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

### 错误处理
```python
if not user_exists(user_id):
    raise HTTPException(
        status_code=404,
        detail="用户不存在"
    )
```

## 🔧 进阶技巧
- **请求/响应拦截器**：用于调试 Header、载荷
- **持久授权**：`persistAuthorization` 保留登录态
- **Monokai 高亮**：阅读代码段更舒适

## 🚀 快速体验
```bash
# 方式一：直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：项目脚本
python run.py
```
启动后打开 `http://localhost:8000/docs` 即可。

使用步骤：
1. 展开目标接口
2. 点击 “Try it out”
3. 填写参数
4. 点击 “Execute” 查看请求/响应

## 📚 参考资料
- FastAPI：https://fastapi.tiangolo.com/
- OpenAPI：https://swagger.io/specification/
- Swagger UI：https://swagger.io/tools/swagger-ui/
- ReDoc：https://redocly.github.io/redoc/

## 🤝 贡献方式
1. 补充路由注释与示例
2. 更新错误响应说明
3. 同步 README/文档中的接口变更
4. 根据业务需要扩展 Swagger 配置

---

**🎉 充分利用 Swagger，让后端联调更顺滑！**
