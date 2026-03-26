# Swagger 使用指南

后端基于 FastAPI 自动生成 OpenAPI 文档，默认暴露 Swagger UI、ReDoc 和 OpenAPI JSON 三个入口。

## 访问地址

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 启动方式

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 建议的使用流程

1. 先通过 `POST /api/v1/auth/login` 获取 token
2. 在 Swagger UI 右上角点击 `Authorize`
3. 输入 `Bearer <token>`
4. 再调试需要鉴权的接口

## 当前主要接口分组

- 认证与权限
- 用户与角色管理
- 股票数据接入
- 指标写入与查询
- 行业分析
- 账户与设置
- 市场数据与涨停复盘
- 投资组合与策略订阅
- 系统健康检查

## 文档维护约定

- 新增路由时补充 `summary`
- 复杂接口补充 `description`
- 输入输出模型尽量使用 Pydantic 明确定义
- 涉及鉴权的接口保留清晰的权限说明
- 接口变更时同步更新 `README.md` 和相关说明文档

## 说明

当前 Swagger 文档以代码为准。若某个 Markdown 文档与 `/openapi.json` 不一致，应优先修正文档而不是猜测接口。
