# JiangEquityRequestAPI

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/WebSocket-realtime-blueviolet?style=for-the-badge&logo=socket.io&logoColor=white"/>
  <img src="https://img.shields.io/badge/LongPort-OpenAPI-FF6B35?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

<p align="center">
  基于 <strong>LongPort OpenAPI</strong> 的股票行情与账户数据后端服务<br/>
  提供 REST + WebSocket 双通道接口，支持行情快照、历史 K 线、基本面、账户持仓与实时推送
</p>

---

> **作者 / Author**  &nbsp;江景哲 · JIANGJINGZHE  
> 📧 [contact@jiangjingzhe.com](mailto:contact@jiangjingzhe.com) &nbsp;|&nbsp; 💬 WeChat: `jiangjingzhe_2004`  
> 🌐 Also see: [www.zero2quant.com](https://www.zero2quant.com) — 量化交易实战课

## 功能概览

| 分类 | 接口 |
|------|------|
| 行情快照 | `GET /api/quotes`、`GET /api/quote/{symbol}` |
| K 线 | `GET /api/candlesticks/{symbol}`（最近 N 根）、`GET /api/candlesticks_range/{symbol}`（按日期区间）|
| 分时 / 盘口 / 成交 | `GET /api/intraday`、`/api/depth`、`/api/trades` |
| 基本面 & 估值 | `GET /api/fundamental`、`/api/static`、`/api/indexes`、`/api/capital` |
| 市场日历 | `GET /api/market/sessions`、`/api/market/trading_days` |
| 账户持仓 | `GET /api/assets/balance`、`/api/assets/positions`、`/api/assets/fund_positions` |
| 自选股 | `GET / POST / DELETE /api/watchlist` |
| 实时推送 | `WS /ws/quotes`（quote / trades / depth / candlestick） |

完整字段说明见 [API.md](API.md)。

---

## 场景示例：获取前复权日 K 线

> 以拉取 **AAPL.US（苹果）2024 年全年前复权日 K 线** 为例，演示从环境准备到拿到数据的完整链路。

**① 设置地址变量**

```bash
export PUBLIC_BASE_URL=http://localhost:8765
```

**② 请求接口**

```bash
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/AAPL.US\
  ?period=day\
  &start=2024-01-01\
  &end=2024-12-31\
  &adjust=forward"
```

**③ 响应（节选）**

```json
[
  {
    "timestamp": 1704153600,
    "open":  "186.090",
    "close": "185.200",
    "high":  "186.740",
    "low":   "183.430",
    "volume": 72162258,
    "turnover": "13346721024.00"
  },
  {
    "timestamp": 1704412800,
    "open":  "183.920",
    "close": "184.400",
    "high":  "185.880",
    "low":   "183.430",
    "volume": 54905516,
    "turnover": "10112345600.00"
  }
]
```

| 参数 | 值 | 说明 |
|------|----|------|
| `period` | `day` | 日 K 线 |
| `start` | `2024-01-01` | 查询起始日期（含） |
| `end` | `2024-12-31` | 查询结束日期（含） |
| `adjust` | `forward` | **前复权**，消除分红送股对价格的影响 |

> 其他可选值：`period` 支持 `1min / 5min / 15min / 30min / 60min / week / month / year`；`adjust` 支持 `none`（不复权）。

---

## 前提条件

| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.11+ | 需支持 `match` 语句和 `asyncio` 改进 |
| pip | 23+ | — |
| LongPort 账户 | — | 需开通 OpenAPI 权限，获取 App Key / App Secret / Access Token |

> 前往 [LongPort OpenAPI 控制台](https://open.longportapp.com) 创建应用并获取凭证。

---

## 本地开发

### 1. 克隆并创建虚拟环境

```bash
git clone <repo-url> JiangEquityRequestAPI
cd JiangEquityRequestAPI

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

用任意编辑器打开 `.env`，**必填**以下三项：

```dotenv
LONGPORT_APP_KEY=your_app_key_here
LONGPORT_APP_SECRET=your_app_secret_here
LONGPORT_ACCESS_TOKEN=your_access_token_here
```

其余配置按需调整（有默认值，不填也能启动）：

```dotenv
SERVER_HOST=0.0.0.0          # 监听地址，本地调试可改为 127.0.0.1
SERVER_PORT=8765              # 监听端口

PUBLIC_BASE_URL=http://localhost:8765   # 服务对外访问地址，供客户端配置使用
WS_BASE_URL=ws://localhost:8765        # WebSocket 对外地址

CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000  # 前端跨域白名单
```

> ⚠️ **`.env` 已加入 `.gitignore`，不会提交到仓库，请勿把真实凭证写入任何其他文件。**

### 3. 启动服务

```bash
python main.py
# 或者指定端口：python main.py --port 9000
```

启动成功后可以看到类似日志：

```
INFO  uvicorn.server - Application startup complete.
INFO  __main__ - JiangEquityRequestAPI backend started.
```

### 4. 验证服务

设置变量（后续命令统一复用）：

```bash
export PUBLIC_BASE_URL=http://localhost:8765
export WS_BASE_URL=ws://localhost:8765
```

```bash
# 健康检查
curl ${PUBLIC_BASE_URL}/health

# 单只行情（港股）
curl "${PUBLIC_BASE_URL}/api/quote/700.HK"

# 批量行情（美股）
curl "${PUBLIC_BASE_URL}/api/quotes?symbols=AAPL.US,NVDA.US,TSLA.US"

# 前复权日 K 线 — 指定时间段（推荐入门示例）
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/AAPL.US?period=day&start=2024-01-01&end=2024-12-31&adjust=forward"

# 也可按最近 N 根拉取（不复权）
curl "${PUBLIC_BASE_URL}/api/candlesticks/AAPL.US?period=day&count=90"

# 账户余额
curl "${PUBLIC_BASE_URL}/api/assets/balance"

# 自选股
curl "${PUBLIC_BASE_URL}/api/watchlist"
```

**WebSocket 实时行情**（需先安装 wscat：`npm install -g wscat`）：

```bash
wscat -c ${WS_BASE_URL}/ws/quotes
# 连接后发送订阅消息：
# {"action":"subscribe","symbols":["700.HK","AAPL.US"]}
```

---

## 生产部署（Ubuntu / EC2）

项目内置一键部署脚本 `deploy.sh`，自动完成 venv、依赖安装、systemd 服务注册与启动。

### 1. 上传代码

```bash
# 本地执行，将整个项目目录上传到服务器
scp -r ./JiangEquityRequestAPI ubuntu@<your-server-ip>:~/JiangEquityRequestAPI
```

或者直接在服务器上拉取：

```bash
ssh ubuntu@<your-server-ip>
git clone <repo-url> ~/JiangEquityRequestAPI
```

### 2. 配置 .env

```bash
cd ~/JiangEquityRequestAPI
cp .env.example .env
nano .env   # 填入真实凭证和服务器公网地址
```

关键字段参考（以 EC2 为例）：

```dotenv
LONGPORT_APP_KEY=<your_key>
LONGPORT_APP_SECRET=<your_secret>
LONGPORT_ACCESS_TOKEN=<your_token>

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
PUBLIC_BASE_URL=http://<your-ec2-public-dns>:8765
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
```

### 3. 运行部署脚本

```bash
bash deploy.sh
```

脚本会自动：
- 安装 Python3（如不存在）
- 创建 `.venv` 并安装依赖
- 注册并启动 systemd 服务 `jiang-equity-request-api`
- 若安装了 `ufw`，自动放行 8765 端口

部署成功输出：

```
✅ 部署成功！服务运行中
   状态: sudo systemctl status jiang-equity-request-api
   日志: sudo journalctl -u jiang-equity-request-api -f
```

### 4. 日常维护

```bash
# 查看服务状态
sudo systemctl status jiang-equity-request-api

# 实时日志
sudo journalctl -u jiang-equity-request-api -f

# 重启服务（更新代码后）
cd ~/JiangEquityRequestAPI
git pull origin main
sudo systemctl restart jiang-equity-request-api

# 停止 / 启动
sudo systemctl stop jiang-equity-request-api
sudo systemctl start jiang-equity-request-api
```

### 5. 验证生产环境

```bash
export PUBLIC_BASE_URL=http://<your-ec2-public-dns>:8765
curl ${PUBLIC_BASE_URL}/health
# 期望返回: {"status":"ok","subscribed":[],"ws_clients":0,"public_base_url":"http://..."}
```

---

## 目录结构

```
JiangEquityRequestAPI/
├── main.py              # FastAPI 入口，lifespan、WebSocket 端点
├── config.py            # 读取 .env 环境变量（凭证 / 端口 / CORS）
├── quote_service.py     # 行情查询 & 实时推送（LongPort AsyncQuoteContext）
├── trade_service.py     # 账户 / 持仓查询（LongPort AsyncTradeContext）
├── websocket_manager.py # WebSocket 连接池 & 广播
├── models.py            # Pydantic 请求 / 响应模型
├── routers/
│   ├── quotes.py        # 行情路由（快照、K 线、盘口、成交、分时）
│   ├── fundamental.py   # 基本面路由（静态信息、估值、资金分布）
│   ├── assets.py        # 账户持仓路由
│   ├── market.py        # 市场日历路由
│   └── watchlist.py     # 自选股路由（JSON 文件持久化）
├── deploy.sh            # Ubuntu 一键部署脚本
├── requirements.txt
├── .env.example         # 环境变量模板（提交到仓库）
├── .env                 # 真实凭证（.gitignore，不提交）
└── API.md               # 完整接口文档（字段说明 + 示例）
```

---

## 常见问题

**Q：启动时报 `KeyError: 'LONGPORT_APP_KEY'`**
→ `.env` 没有正确填写或没有执行 `cp .env.example .env`，检查文件是否存在且三个凭证字段不为空。

**Q：接口返回 500 `internal server error`**
→ 详细原因在服务端日志中，本地查看：`python main.py` 的终端输出；生产环境查看：`sudo journalctl -u jiang-equity-request-api -f`。

**Q：WebSocket 连接后收不到推送**
→ 需先发送订阅消息 `{"action":"subscribe","symbols":["700.HK"]}`，服务端不会主动推送未订阅的标的。

**Q：CORS 被浏览器拦截**
→ 在 `.env` 中把前端来源加入 `CORS_ALLOW_ORIGINS`，逗号分隔多个来源。
