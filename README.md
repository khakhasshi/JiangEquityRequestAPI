# JiangEquityRequestAPI

基于 **LongPort OpenAPI** 的股票行情与账户数据后端服务，使用 FastAPI + WebSocket 构建。

## 技术栈

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 实时推送 | WebSocket（FastAPI 原生） |
| 数据源 | LongPort OpenAPI SDK (`longport`) |
| 异步模型 | Python asyncio |

## 功能概览

| 分类 | 接口 |
|------|------|
| 行情快照 | `GET /api/quotes`、`GET /api/quote/{symbol}` |
| K 线数据 | `GET /api/candlesticks/{symbol}`（最近 N 根）、`GET /api/candlesticks_range/{symbol}`（按日期区间） |
| 分时 / 盘口 / 成交 | `/api/intraday`、`/api/depth`、`/api/trades` |
| 市场日历 | `GET /api/market/sessions`、`GET /api/market/trading_days` |
| 基本面 & 估值 | `/api/fundamental`、`/api/static`、`/api/indexes`、`/api/capital` |
| 账户持仓 | `/api/assets/balance`、`/api/assets/positions`、`/api/assets/fund_positions` |
| 自选股 | `GET/POST/DELETE /api/watchlist` |
| 实时推送 | `WS /ws/quotes`（quote / trades / depth / candlestick） |

完整接口文档见 [API.md](API.md)。

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone <repo-url> JiangEquityRequestAPI
cd JiangEquityRequestAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置凭证

```bash
cp .env.example .env
# 编辑 .env，填入 LongPort App Key / Secret / Access Token
# 可选：配置 PUBLIC_BASE_URL（对外访问地址）
# 可选：配置 CORS_ALLOW_ORIGINS（逗号分隔）
```

### 3. 启动服务

```bash
python main.py
# 服务默认监听 http://0.0.0.0:8765
```

### 4. 配置请求地址变量（推荐）

```bash
export PUBLIC_BASE_URL=http://localhost:8765
export WS_BASE_URL=ws://localhost:8765
```

### 5. 验证

```bash
curl ${PUBLIC_BASE_URL}/health
curl "${PUBLIC_BASE_URL}/api/quote/AAPL.US"
# WebSocket 测试示例
# wscat -c ${WS_BASE_URL}/ws/quotes
```

## 目录结构

```
JiangEquityRequestAPI/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置（读取环境变量）
├── quote_service.py     # 行情服务（WS 订阅 + 查询）
├── trade_service.py     # 交易/账户服务
├── websocket_manager.py # WS 连接管理
├── models.py            # Pydantic 数据模型
├── routers/
│   ├── quotes.py        # 行情路由
│   ├── fundamental.py   # 基本面路由
│   ├── assets.py        # 账户持仓路由
│   ├── market.py        # 市场日历路由
│   └── watchlist.py     # 自选股路由
├── requirements.txt
├── .env.example
└── API.md               # 完整接口文档
```

## 部署（EC2）

```bash
# 服务器上（确保 .env 已配置）
cd ~/JiangEquityRequestAPI
git pull origin main
pkill -f 'python.*main.py'
nohup .venv/bin/python main.py > /tmp/api.log 2>&1 &
```
