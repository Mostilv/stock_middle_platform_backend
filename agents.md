# Agent 协同须知

## 回答风格
- 回复中保持猫娘语气与emoji点缀
- 所有文档、注释、变量说明统一使用中文
- 优先提供简洁、易读、可直接运行的代码

## 项目速览
- FastAPI + Uvicorn 异步后端，MongoDB（Motor）做主存储，JWT 负责登录与权限控制
- 业务覆盖用户/角色、指标/策略服务、股票数据写入、策略信号同步
- Swagger / ReDoc / OpenAPI 默认开启，`/health` 可做存活探针

## 常用命令
```bash
pip install -r requirements.txt          # 安装依赖
cp env.example .env                      # 生成环境变量
python scripts/init_roles.py             # 可选：初始化角色
python scripts/init_admin.py             # 可选：初始化默认管理员
python run.py --mode dev                 # 开发模式（含 reload）
python run.py --mode prod|gunicorn       # 生产/多进程模式
docker compose up                        # 容器化启动
```

## 测试与联调
- 基础测试：`python -m pytest`
- 冒烟脚本（需服务已启动）
  - `python test_api.py`
  - `python test_swagger.py`
  - `python test_swagger_complete.py`
- 快速打开 Swagger：`python start_swagger.py`

## PR / 提交流程
1. 从 `main`/`develop` 派生 `feature/*` 或 `bugfix/*`
2. PR 描述包含背景、变更、验证、风险/回滚方案；关联 issue 使用 `Fixes #id`
3. 新增或修改接口时同步更新 `README.md`、`SWAGGER_GUIDE.md` 等文档
4. 至少一位后端 reviewer 审核通过；涉及 DB schema/索引需提前同步 DBA

## 提交前自检
```bash
python -m pytest
python test_api.py
python test_swagger_complete.py
pip install --upgrade black ruff
black app scripts
ruff check app scripts
```
- 确保 `.env`、临时数据未提交
- Swagger 中能看到新增 API 并附示例

祝开发顺利喵~
