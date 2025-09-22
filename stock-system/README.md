# Stock System

一套可在低配置服务器上运行的个人量化后端与任务服务，实现 A 股数据采集、指标计算、聚宽信号中转、邮件推送与 FastAPI Web API。

## 功能概览

- **数据采集**：封装 Baostock / AkShare 适配器，统一抽象，支持日常增量更新 K 线、基础信息及指标入库（MongoDB）。
- **指标体系**：内置 MA / RSI / MACD / ATR / BOLL，支持自定义指标注册与计算，结果写入 MongoDB。
- **信号与调仓**：聚宽 Webhook（HMAC 校验）入库 MySQL，提供持仓、信号、调仓计划查询与确认接口。
- **调度与自动化**：APScheduler 进程内调度 + systemd timer 双保险，支持 `python -m app.scheduler.cli --once daily`。
- **通知邮件**：渲染当日信号、持仓及指标快照，通过 SMTP 发送并记录日志。
- **Web API**：FastAPI + Uvicorn，统一 API-Key 鉴权、分页与错误格式，提供 OpenAPI 文档。

## 目录结构

```
stock-system/
  app/
    api/              # 路由与依赖
    service/          # 领域服务
    repo/             # MySQL & Mongo 访问层
    datasource/       # 数据源适配器
    indicators/       # 指标实现与注册
    scheduler/        # APScheduler 与 CLI
    utils/            # 通用工具
  scripts/            # 引导、种子、索引、systemd 文件
  tests/              # Pytest 用例
  README.md
  requirements.txt
  pyproject.toml
  docker-compose.yml
  Makefile
  .env.example
```

## 快速开始

### 本地开发

```bash
cd stock-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 根据实际填写 API_KEY、数据库、SMTP 等
python scripts/create_indexes.py
python scripts/seed_demo_data.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --loop uvloop --http h11
```

访问 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档。

### Docker Compose

```bash
cd stock-system
docker compose up -d --build
```

服务默认监听 `0.0.0.0:8000`，MySQL 暴露 3306，Mongo 暴露 27017。首次启动后执行：

```bash
docker compose exec api python scripts/create_indexes.py
docker compose exec api python scripts/seed_demo_data.py
```

## 环境变量 `.env`

| Key | 描述 |
| --- | --- |
| `API_KEY` | 所有受保护 API 的访问密钥 |
| `SECRET_KEY` | Webhook HMAC 校验密钥 |
| `MYSQL_*` | MySQL 连接信息（生产建议外部托管或自建） |
| `MONGO_URI` / `MONGO_DB` | MongoDB 连接与库名 |
| `SMTP_*` | 邮件 SMTP 服务器配置 |
| `MAIL_TO` | 默认邮件收件人 |
| `TZ` | 时区，默认 `Asia/Shanghai` |

开发环境默认使用内存 Mongo 与 sqlite（通过测试装置自动覆盖）。

## 关键命令（Makefile）

- `make dev`：创建虚拟环境并安装依赖。
- `make run`：本地启动 Uvicorn。
- `make fmt`：black + ruff 自动格式化。
- `make lint`：ruff + mypy 静态检查。
- `make test`：运行 Pytest。
- `make seed`：写入演示数据。
- `make indexes`：创建 MySQL / Mongo 索引。

## API 鉴权与安全

- 除 `/healthz` 外所有接口需 `X-API-Key`。`routes_webhook_jq` 额外要求：
  - `X-Signature`: `base64(hmac_sha256(secret, timestamp.payload))`
  - `X-Timestamp`: 秒级时间戳，允许 ±120s 漂移。
- 默认 Uvicorn 仅监听 `127.0.0.1`。生产建议使用 Nginx 反向代理 + 限流：

```nginx
server {
  listen 80;
  server_name your.domain;

  limit_req_zone $binary_remote_addr zone=stock_limit:10m rate=10r/s;

  location / {
    limit_req zone=stock_limit burst=20;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
```

## 数据调度

- APScheduler 在应用内注册，每日 17:30 执行数据刷新 → 指标计算 → 邮件发送。
- `python -m app.scheduler.cli --once daily` 可手动触发完整流程。
- systemd timer (`scripts/systemd/`) 提供守护配置：
  - `stock_api.service`：常驻 API。
  - `stock_worker.service`：按需执行 CLI。
  - `stock_timer_refresh.timer`/`.service`：每天 17:30 触发。

部署示例：

```bash
sudo cp scripts/systemd/*.service scripts/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stock_api.service stock_timer_refresh.timer
```

日志查看：

```bash
journalctl -u stock_api -f
journalctl -u stock_timer_refresh -f
```

## 邮件服务

- `POST /tasks/mail/preview`：返回 HTML 预览。
- `POST /tasks/mail/send-today`：发送今日摘要（`ENV=prod` 时才会调用真实 SMTP）。
- 发送结果写入 `mail_log`（MySQL）。

## 自定义指标

1. 定义：`POST /indicators/custom/define`
2. 计算：`POST /indicators/custom/compute`
3. 查询：`GET /indicators/custom/query`

示例实现位于 `app/indicators/custom/momentum_v1.py`。

## 最小前端示例

```javascript
// 取 K 线与 5/20 日均线
await fetch(`/stocks/600519/kline?period=daily&start=2025-06-01&adjust=qfq&limit=500`, {
  headers: {"X-API-Key": "<your_key>"}
});
await fetch(`/stocks/600519/technicals?names=MA,RSI&start=2025-06-01`, {
  headers: {"X-API-Key": "<your_key>"}
});

// 当前持仓
await fetch(`/positions/current`, { headers: {"X-API-Key": "<your_key>"} });

// 自定义指标查询
await fetch(`/indicators/custom/query?code=600519&indicator=MY_MOM&start=2025-06-01`, {
  headers: {"X-API-Key": "<your_key>"}
});
```

## 部署到阿里云轻量应用服务器（Ubuntu 22.04 / 1C2G）

```bash
sudo apt update && sudo apt install -y python3.10-venv git nginx
sudo useradd -m stock && sudo passwd stock
sudo su - stock

git clone <repo> ~/stock-system && cd ~/stock-system
cp .env.example .env && nano .env  # 填写 API_KEY、SECRET_KEY、数据库、SMTP 等
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/create_indexes.py
python scripts/seed_demo_data.py

# systemd
sudo cp scripts/systemd/*.service scripts/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stock_api.service stock_timer_refresh.timer

# Nginx 反代
sudo tee /etc/nginx/sites-available/stock <<'NGINX'
server {
  listen 80;
  server_name your.domain;
  limit_req_zone $binary_remote_addr zone=stock_limit:10m rate=10r/s;
  location / {
    limit_req zone=stock_limit burst=20;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/stock /etc/nginx/sites-enabled/stock
sudo nginx -t && sudo systemctl reload nginx
```

监控命令：

```bash
journalctl -u stock_api -f
journalctl -u stock_timer_refresh -f
```

## 常见问题

- **Baostock 登录失败 / 限流**：当前实现包含退避和重试占位逻辑，生产环境需替换为真实 SDK。节假日无数据时返回空列表，系统自动跳过。
- **AkShare 首次调用较慢**：官方库会下载元数据，建议在部署后预热或缓存。
- **内存不足**：使用 `uvicorn --workers 1 --loop uvloop --http h11`，并精简依赖。
- **数据库未启动**：脚本提供 `scripts/create_indexes.py` 和 `scripts/seed_demo_data.py` 快速初始化。

## 质量与测试

- 代码风格：black、ruff、mypy。
- 单元测试：`pytest`（6 个核心用例覆盖健康检查、指标、K 线、自定义指标、Webhook、持仓聚合）。
- 日志：结构化（JSON 可选），区分 INFO / ERROR。

## 验收路径

1. `GET /healthz` → `{"status":"ok"}`。
2. `POST /tasks/refresh-daily` → 拉取并写入至少一个代码的日线。
3. `POST /tasks/compute-indicators` → 计算 MA(5) / RSI(14)。
4. `POST /webhook/jq/signal` → 信号写入 MySQL，`GET /signals/recent` 可查询。
5. `GET /positions/current` → 返回持仓聚合。
6. 自定义指标闭环：定义 → 计算 → 查询。
7. `GET /fundamentals/{code}` → 返回核心财务指标。
8. 调仓链路：`GET /rebalance/plans` → `GET /rebalance/{plan_id}` → `POST /rebalance/confirm`。
9. 邮件：`POST /tasks/mail/preview` / `POST /tasks/mail/send-today`（记录 mail_log）。
10. `pytest` 全部通过。

