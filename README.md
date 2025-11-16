# 股票中台后端

## 概述
- 基于 FastAPI 构建的股票中台后端，负责用户/角色管理、指标接入、策略服务与数据推送。
- MongoDB 搭配 Motor 异步驱动提供主要数据存储，读写均支持协程化处理。
- 默认启用 JWT 认证与角色/权限校验，并自动生成 Swagger 文档方便联调。

## 技术栈
- FastAPI + Uvicorn
- MongoDB（Motor 异步驱动）
- 可选：Redis / Celery 处理后台任务
- Python-JOSE + Passlib 负责 JWT/密码哈希

## 分层架构
后端采用三层结构：
- `app/controllers`：路由与请求响应处理（FastAPI Router）。
- `app/services`：业务逻辑、事务编排。
- `app/repositories`：与 MongoDB 交互的数据访问层。

公共配置、领域模型与工具函数分别位于 `app/config`、`app/models`、`app/utils`。

## 项目结构
```
|-- app
|   |-- controllers
|   |   |-- auth.py
|   |   |-- data_feed.py
|   |   |-- indicators.py
|   |   |-- roles.py
|   |   |-- strategies.py
|   |   |-- users.py
|   |   +-- __init__.py
|   |-- services
|   |   |-- indicator_service.py
|   |   |-- qlib_data_service.py
|   |   |-- role_service.py
|   |   |-- strategy_service.py
|   |   |-- user_service.py
|   |   +-- __init__.py
|   |-- repositories
|   |   |-- base.py
|   |   |-- indicator_repository.py
|   |   |-- qlib_data_repository.py
|   |   |-- role_repository.py
|   |   |-- strategy_repository.py
|   |   |-- user_repository.py
|   |   +-- __init__.py
|   |-- config.py
|   |-- core
|   |-- db
|   |-- example
|   |-- main.py
|   |-- models
|   |   |-- indicator.py
|   +-- utils
|-- scripts
|-- env.example
|-- requirements.txt
|-- docker-compose.yml / Dockerfile
|-- run.py / start.{bat,sh}
|-- SWAGGER_GUIDE.md / SWAGGER_INTEGRATION_SUMMARY.md
|-- test_api.py / test_swagger*.py
|-- uvicorn_config.py
```

历史上的 `stock-system/` 子目录已移除，避免嵌套项目混乱。

## 快速上手
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量
   ```bash
   cp env.example .env
   # 按需调整 MongoDB / JWT / 数据源配置
   ```
3. （可选）写入初始数据
   ```bash
   python scripts/init_roles.py
   python scripts/init_admin.py  # 默认 admin/admin123
   ```
4. 启动服务
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   也可运行 `run.py`、`start.sh` 或 `start.bat`。

## 常用接口
- Swagger UI：`/docs`
- ReDoc：`/redoc`
- OpenAPI：`/openapi.json`
- 健康检查：`/health`
- Qlib 数据写入：`POST /api/v1/data/qlib/bars`（需 Bearer Token）
- 指标写入：`POST /api/v1/indicators/records`（需 `indicators:write`）
- 指标查询：`GET /api/v1/indicators/records`（需 `indicators:read`）
- 股票基础数据：`POST /api/v1/stocks/basic`（需 `stocks:write`）
- 股票 K 线：`POST /api/v1/stocks/kline`（需 `stocks:write`）
- 数据目标 Schema：`GET /api/v1/stocks/targets`（需 `stocks:read`）
- 行业指标聚合：`GET /api/v1/analytics/industry/metrics`（需 `indicators:read`）

## Qlib 数据接入
`/api/v1/data/qlib/bars` 兼容 [Microsoft Qlib](https://github.com/microsoft/qlib) 的字段命名，载荷需包含 Bearer Token。

```bash
curl -X POST http://localhost:8000/api/v1/data/qlib/bars \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "provider": "partner-feed",
        "market": "cn",
        "timezone": "Asia/Shanghai",
        "records": [
          {
            "instrument": "SH600519",
            "datetime": "2024-10-08T15:00:00+08:00",
            "freq": "1d",
            "open": 1600.5,
            "high": 1611.2,
            "low": 1590.0,
            "close": 1605.4,
            "volume": 123456,
            "amount": 987654321,
            "factor": 1.0,
            "turnover": 0.35,
            "limit_status": "none",
            "suspended": false,
            "extra_fields": {
              "Ref(close,1)": 1588.1
            }
          }
        ]
      }'
```

服务会把股票代码转换为大写、统一时间为 UTC，并在 `(instrument, freq, datetime)` 复合键上 upsert，重复推送保持幂等。

## 指标数据推送与查询
指标计算由外部组件承担，本服务负责接收、存储与查询：
- 写入：`POST /api/v1/indicators/records`
  - 需 `indicators:write`
  - 支持批量 upsert，同一 `(indicator, symbol, timeframe, timestamp)` 自动覆盖
  - `value`、`values`、`payload` 至少提供一个
- 查询：`GET /api/v1/indicators/records`
  - 需 `indicators:read`
  - 支持按指标、标的、时间区间、标签过滤
  - 返回 `data + total` 结构方便前端分页

```bash
curl -X POST http://localhost:8000/api/v1/indicators/records \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "provider": "quant-service",
        "records": [
          {
            "symbol": "SH600519",
            "indicator": "rsi14",
            "timeframe": "1d",
            "timestamp": "2024-10-08T15:00:00+08:00",
            "value": 56.17,
            "values": {"overbought": 70, "oversold": 30},
            "payload": {"window": 14},
            "tags": ["daily", "demo"]
          }
        ]
      }'
```

```bash
curl -G http://localhost:8000/api/v1/indicators/records \
  -H "Authorization: Bearer <token>" \
  --data-urlencode "indicator=rsi14" \
  --data-urlencode "symbol=SH600519" \
  --data-urlencode "timeframe=1d" \
  --data-urlencode "limit=50"
```

## 默认账号
- 用户名：`admin`
- 密码：`admin123`
- 权限：继承 `admin` 角色，首次登录后请立即修改密码。

## 股票数据推送流程
- 通过 `GET /api/v1/stocks/targets`（需 `stocks:read`）查看可用逻辑库/集合及 JSON Schema（`stock_basic`、`stock_kline`、`indicator` 等）。管理员可用 `DATA_TARGETS` 环境变量自定义映射。
- `POST /api/v1/stocks/basic`、`POST /api/v1/stocks/kline`（需 `stocks:write`）用于推送基础信息与多频 K 线，请确保载荷含 `target`、`provider`、`items`；格式出错会返回 400 并附参考 Schema。
- 行业指标继续通过 `POST /api/v1/indicators/records` 写入，可在 `target` 字段指定存储目标。

## 行业指标聚合接口
`GET /api/v1/analytics/industry/metrics`（需 `indicators:read`）会基于入库指标数据聚合申万一级行业的动量、宽度：
- 查询参数：`days`（默认 12）、`target`、`end`（ISO8601，可与前端日期控件配合）。
- 响应提供 `dates` 与 `series` 数组，前端即可直接绘制折线图或热力图。
