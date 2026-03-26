# 协作说明

本文档用于说明在本后端仓库内协作时的基本约定。

## 文档要求

- 统一使用中文
- 以当前代码结构为准，不保留已经失效的目录说明
- 接口变更时同步更新 `README.md` 与 Swagger 相关文档

## 开发重点

- 主入口是 `app/main.py`
- 核心分层在 `controllers`、`services`、`repositories`
- 认证和权限逻辑位于 `app/core`
- 数据库连接与生命周期位于 `app/db`

## 提交前建议检查

```bash
python -m pytest
```

如果项目内保留了接口联调脚本，也建议一并执行。

## 维护提醒

- 不要再新增乱码或过期文档
- 新增模块时优先补 README 或模块说明
- 文档中的接口示例应尽量与 `/openapi.json` 保持一致
