# Swagger 集成现状

当前后端已经集成 Swagger UI、ReDoc 和 OpenAPI JSON，文档入口由 FastAPI 自动生成。

## 已完成内容

- `app/main.py` 已挂载 Swagger 相关入口
- `app/utils/swagger_config.py` 用于集中管理 Swagger 配置
- 接口模型通过 Pydantic 暴露到 OpenAPI 文档
- 支持 Bearer Token 鉴权调试

## 当前价值

- 前后端联调可以直接基于 `/docs`
- OpenAPI JSON 可用于后续生成 SDK 或契约校验
- 新接口只要按 FastAPI 规范声明即可自动出现在文档中

## 后续建议

1. 为关键接口补充更清晰的 `summary` 与 `description`
2. 为高频接口补充请求示例和错误示例
3. 在 CI 中加入对 `/openapi.json` 可用性的检查
