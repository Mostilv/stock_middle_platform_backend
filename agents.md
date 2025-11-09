# Codex Agent Notes

## 项目速览
- FastAPI + Uvicorn 异步后端, MongoDB (Motor) 持久化, JWT 登录/权限控制。
- 主要业务: 用户/角色管理、指标与策略服务、Qlib 数据写入 (`POST /api/v1/data/qlib/bars`)。
- Swagger/Redoc/OpenAPI 已开启, `/health` 可用作存活探针。

## 常用命令
```bash
pip install -r requirements.txt         # 准备依赖
cp env.example .env                     # 配置环境变量
python scripts/init_roles.py            # 可选: 初始化角色
python scripts/init_admin.py            # 可选: 初始化默认管理员
python run.py --mode dev                # 开发模式启动 (含 reload)
python run.py --mode prod|gunicorn      # 生产/多进程
docker compose up                       # 容器化启动
```

## 测试/联调
- 单元与服务测试: `python -m pytest`
- 冒烟脚本(需本地服务运行):
  - `python test_api.py`
  - `python test_swagger.py`
  - `python test_swagger_complete.py`
- Swagger 快捷启动: `python start_swagger.py` (另一终端)

## PR / 提交要求
1. 分支从 `main`/`develop` 派生, 命名 `feature/*`、`bugfix/*`。
2. PR 描述包含背景、改动、验证、风险/回滚; 修复 issue 时写 `Fixes #id`。
3. 新增/修改接口更新对应文档 (`README.md`, `SWAGGER_GUIDE.md` 等)。
4. 至少一名后端 reviewer 通过方可合并, 涉 DB schema/索引需提前同步 DBA。

## 提交前自查
```bash
python -m pytest
python test_api.py
python test_swagger_complete.py
pip install --upgrade black ruff
black app scripts
ruff check app scripts
```
- 确认 `.env`、临时数据未入库; 新 API 已在 Swagger 中可见并有示例。
