# JiangEquityRequestAPI 后端 API 文档

**Base URL**: 建议通过环境变量配置：`PUBLIC_BASE_URL`（HTTP）与 `WS_BASE_URL`（WebSocket）  
**协议**: HTTP REST + WebSocket  
**数据格式**: JSON

推荐在本地 shell 里先设置：

```bash
export PUBLIC_BASE_URL=http://localhost:8765
export WS_BASE_URL=ws://localhost:8765
```

---

## 目录

- [健康检查](#健康检查)
- [行情接口](#行情接口)
  - [批量行情快照](#批量行情快照)
  - [单只行情快照](#单只行情快照)
  - [历史 K 线](#历史-k-线)
  - [按时间段查 K 线](#按时间段查-k-线)
  - [盘口深度](#盘口深度)
  - [逐笔成交](#逐笔成交)
  - [分时数据](#分时数据)
  - [订阅推送](#订阅推送)
  - [取消订阅](#取消订阅)
- [基本面接口](#基本面接口)
  - [合并基本面](#合并基本面)
  - [静态信息](#静态信息)
  - [估值指标](#估值指标)
  - [资金分布](#资金分布)
- [资产接口](#资产接口)
  - [账户余额](#账户余额)
  - [股票持仓](#股票持仓)
  - [基金持仓](#基金持仓)
- [自选股接口](#自选股接口)
  - [获取自选股](#获取自选股)
  - [添加自选股](#添加自选股)
  - [删除自选股](#删除自选股)
- [市场日历接口](#市场日历接口)
  - [交易时段](#交易时段)
  - [交易日历](#交易日历)
- [WebSocket 实时推送](#websocket-实时推送)

---

## 健康检查

### `GET /health`

检查服务是否正常运行。

**响应**

```json
{
  "status": "ok",
  "subscribed": ["700.HK", "AAPL.US"],
  "ws_clients": 2,
  "public_base_url": "http://localhost:8765"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 固定为 `"ok"` |
| `subscribed` | string[] | 当前已订阅实时推送的标的列表 |
| `ws_clients` | int | 当前连接的 WebSocket 客户端数量 |
| `public_base_url` | string | （可选）服务对外地址，配置了 `PUBLIC_BASE_URL` 时返回 |

**示例**

```bash
curl ${PUBLIC_BASE_URL}/health
```

---

## 行情接口

### 批量行情快照

### `GET /api/quotes`

批量获取多只股票的实时行情快照。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ✅ | 股票代码，逗号分隔，如 `700.HK,AAPL.US` |

**响应** — `StockQuote[]`

```json
[
  {
    "symbol": "AAPL.US",
    "name": "AAPL.US",
    "last_done": "189.820",
    "open": "187.500",
    "high": "190.100",
    "low": "187.200",
    "prev_close": "188.500",
    "volume": 45231890,
    "turnover": "8534912345.00",
    "change": "1.320",
    "change_pct": "0.70",
    "timestamp": 1771621140,
    "is_up": true
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `symbol` | string | 股票代码 |
| `name` | string | 股票名称 |
| `last_done` | string | 最新价 |
| `open` | string | 今日开盘价 |
| `high` | string | 今日最高价 |
| `low` | string | 今日最低价 |
| `prev_close` | string | 昨日收盘价 |
| `volume` | int | 成交量（股） |
| `turnover` | string | 成交额 |
| `change` | string | 涨跌额 |
| `change_pct` | string | 涨跌幅（%），如 `"0.70"` 表示 +0.70% |
| `timestamp` | int | 行情时间（Unix 秒） |
| `is_up` | bool | `true` 表示上涨或平盘 |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/quotes?symbols=700.HK,AAPL.US,NVDA.US"
```

---

### 单只行情快照

### `GET /api/quote/{symbol}`

获取单只股票实时行情。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码，如 `NVDA.US`、`700.HK` |

**响应** — 单个 `StockQuote` 对象（字段同上）

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/quote/NVDA.US"
```

---

### 历史 K 线

### `GET /api/candlesticks/{symbol}`

获取指定股票的历史 K 线数据，从当前时间向前取。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**Query 参数**

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `period` | ❌ | `day` | K 线周期，见下表 |
| `count` | ❌ | `90` | 返回条数，最大受 LongPort 限制 |

**`period` 枚举值**

| 值 | 说明 |
|----|------|
| `1min` | 1 分钟 |
| `5min` | 5 分钟 |
| `15min` | 15 分钟 |
| `30min` | 30 分钟 |
| `60min` | 60 分钟 |
| `day` | 日 K |
| `week` | 周 K |
| `month` | 月 K |
| `year` | 年 K |

**响应** — `Candlestick[]`，按时间**从早到晚**排列

```json
[
  {
    "timestamp": 1771609200,
    "open": "188.370",
    "close": "188.364",
    "high": "188.500",
    "low": "188.200",
    "volume": 342100,
    "turnover": "64512345.00"
  },
  {
    "timestamp": 1771609260,
    "open": "188.364",
    "close": "188.510",
    "high": "188.600",
    "low": "188.300",
    "volume": 278900,
    "turnover": "52634120.00"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | int | K 线开始时间（Unix 秒） |
| `open` | string | 开盘价 |
| `close` | string | 收盘价 |
| `high` | string | 最高价 |
| `low` | string | 最低价 |
| `volume` | int | 成交量（股） |
| `turnover` | string | 成交额 |

**示例**

```bash
# 获取 NVDA 最近 200 根 1 分钟 K 线
curl "${PUBLIC_BASE_URL}/api/candlesticks/NVDA.US?period=1min&count=200"

# 获取 700.HK 最近 90 根日 K
curl "${PUBLIC_BASE_URL}/api/candlesticks/700.HK?period=day&count=90"
```

---

### 按时间段查 K 线

### `GET /api/candlesticks_range/{symbol}`

获取指定开始 / 结束时间范围内的全部 K 线。与 `/api/candlesticks` 的区别是：前者按最新 N 根倒取，后者按日期区间取全㟏。

**路径参数**

| 参数 | 说明 |
|------|---------|
| `symbol` | 股票代码，如 `AAPL.US`、`700.HK` |

**查询参数**

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `period` | string | 否 | `day` | K 线周期：`1min` / `5min` / `15min` / `30min` / `60min` / `day` / `week` / `month` / `year` |
| `start` | string | 否 | 无（取全部） | 开始日期，格式 `YYYY-MM-DD`（推荐）或 `YYYY-MM-DDTHH:MM:SS`（只取日期部分） |
| `end` | string | 否 | 无（取全部） | 结束日期，格式同上 |
| `adjust` | string | 否 | `none` | 复权方式：`none`（不复权）/ `forward`（前复权） |

> `start` / `end` 均不传时返回该标的全部历史（受 SDK 数据量限制）。时间部分（`THH:MM:SS`）会被忽略，建议只传日期。

**响应**：格式与 `/api/candlesticks` 完全相同

```json
[
  {
    "timestamp": 1735689600,
    "open":  "220.150",
    "close": "223.080",
    "high":  "223.540",
    "low":   "219.870",
    "volume": 45123400,
    "turnover": "10034521200.00"
  }
]
```

**示例**

```bash
# 获取 AAPL.US 2025 年全年日 K
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/AAPL.US?period=day&start=2025-01-01&end=2025-12-31"

# 获取 700.HK 2025-02-03 全天 1 分钟 K
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/700.HK?period=1min&start=2025-02-03&end=2025-02-03"

# 获取 NVDA.US 2025-02-01 全天 15 分钟 K，前复权（时间部分会被忽略，只传日期即可）
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/NVDA.US?period=15min&start=2025-02-01&end=2025-02-07&adjust=forward"

# 不传时间范围，取全部日 K
curl "${PUBLIC_BASE_URL}/api/candlesticks_range/SPY.US?period=week"
```

---

### 盘口深度

### `GET /api/depth/{symbol}`

获取股票买卖盘口十档数据。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**响应**

```json
{
  "symbol": "700.HK",
  "asks": [
    { "price": "385.60", "volume": 12000, "order_num": 5 },
    { "price": "385.80", "volume": 34500, "order_num": 12 }
  ],
  "bids": [
    { "price": "385.40", "volume": 8800, "order_num": 3 },
    { "price": "385.20", "volume": 21000, "order_num": 8 }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `asks` | DepthLevel[] | 卖盘，按价格从低到高排列 |
| `bids` | DepthLevel[] | 买盘，按价格从高到低排列 |
| `price` | string | 档位价格 |
| `volume` | int | 挂单量（股） |
| `order_num` | int | 委托笔数 |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/depth/700.HK"
```

---

### 逐笔成交

### `GET /api/trades/{symbol}`

获取指定股票最近 N 笔成交明细。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**Query 参数**

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `count` | ❌ | `100` | 返回笔数，范围 1–1000 |

**响应** — `Trade[]`，按时间**从早到晚**排列

```json
[
  {
    "price": "189.990",
    "volume": 100,
    "timestamp": 1771621197,
    "direction": "Down",
    "trade_type": "I",
    "trade_session": "Post"
  },
  {
    "price": "190.010",
    "volume": 300,
    "timestamp": 1771621200,
    "direction": "Up",
    "trade_type": " ",
    "trade_session": "Normal"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `price` | string | 成交价 |
| `volume` | int | 成交量（股） |
| `timestamp` | int | 成交时间（Unix 秒） |
| `direction` | string | 成交方向：`Up`（主动买）/ `Down`（主动卖）/ `Neutral` |
| `trade_type` | string | 成交类型代码（交易所定义，空格为普通成交） |
| `trade_session` | string | 交易时段：`Normal`（正常）/ `Pre`（盘前）/ `Post`（盘后）/ `Overnight` |

**示例**

```bash
# 最近 200 笔成交
curl "${PUBLIC_BASE_URL}/api/trades/NVDA.US?count=200"

# 港股
curl "${PUBLIC_BASE_URL}/api/trades/700.HK?count=100"
```

---

### 分时数据

### `GET /api/intraday/{symbol}`

获取当日完整分时数据（每分钟一个数据点），用于绘制分时图。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**响应** — `IntradayPoint[]`，按时间**从早到晚**排列

```json
[
  {
    "timestamp": 1771580400,
    "price": "186.170",
    "avg_price": "186.465",
    "volume": 3952930,
    "turnover": "737083820.85"
  },
  {
    "timestamp": 1771580460,
    "price": "186.320",
    "avg_price": "186.480",
    "volume": 2341200,
    "turnover": "436721543.20"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | int | 分钟起始时间（Unix 秒） |
| `price` | string | 该分钟收盘价（分时价） |
| `avg_price` | string | 截至该分钟的当日均价 |
| `volume` | int | 该分钟成交量（股） |
| `turnover` | string | 该分钟成交额 |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/intraday/NVDA.US"
```

---

### 订阅推送

### `POST /api/subscribe`

通过 REST 触发服务端对指定标的的实时推送订阅（WebSocket 客户端随后会收到推送）。

**请求体**

```json
{ "symbols": ["700.HK", "AAPL.US"] }
```

**响应**

```json
{ "subscribed": ["700.HK", "AAPL.US", "NVDA.US"] }
```

**示例**

```bash
curl -X POST "${PUBLIC_BASE_URL}/api/subscribe" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["700.HK", "AAPL.US"]}'
```

---

### 取消订阅

### `DELETE /api/subscribe/{symbol}`

取消单只标的的实时推送订阅。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**响应**

```json
{ "subscribed": ["AAPL.US"] }
```

**示例**

```bash
curl -X DELETE "${PUBLIC_BASE_URL}/api/subscribe/700.HK"
```

---

## 基本面接口

### 合并基本面

### `GET /api/fundamental`

合并返回静态信息 + 估值指标，一次请求获取完整基本面数据。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ✅ | 股票代码，逗号分隔 |

**响应** — 静态信息与估值指标合并后的对象数组，字段为以下两节的并集。

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/fundamental?symbols=700.HK,AAPL.US"
```

---

### 静态信息

### `GET /api/static`

获取股票静态基本面：名称、股本、EPS、BPS、股息率等。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ✅ | 股票代码，逗号分隔 |

**响应**

```json
[
  {
    "symbol": "700.HK",
    "name_cn": "腾讯控股",
    "name_en": "TENCENT",
    "name_hk": "騰訊控股",
    "exchange": "SEHK",
    "currency": "HKD",
    "lot_size": 100,
    "total_shares": 9541044936,
    "circulating_shares": 9390000000,
    "hk_shares": 9390000000,
    "eps": "17.23",
    "eps_ttm": "18.05",
    "bps": "140.98",
    "dividend_yield": "0.85",
    "stock_derivatives": ["WARRANT", "CBBC"]
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `name_cn` / `name_en` / `name_hk` | string | 中/英/繁体名称 |
| `exchange` | string | 交易所代码 |
| `currency` | string | 交易货币 |
| `lot_size` | int | 每手股数 |
| `total_shares` | int | 总股本 |
| `circulating_shares` | int | 流通股本 |
| `hk_shares` | int | 港股股本（HK 市场专用） |
| `eps` | string | 每股收益 |
| `eps_ttm` | string | 过去12个月每股收益 |
| `bps` | string | 每股净资产 |
| `dividend_yield` | string | 股息率（%） |
| `stock_derivatives` | string[] | 衍生品类型列表 |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/static?symbols=700.HK,AAPL.US"
```

---

### 估值指标

### `GET /api/indexes`

获取 PE、PB、各周期涨跌幅等估值与技术指标。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ✅ | 股票代码，逗号分隔 |

**响应**

```json
[
  {
    "symbol": "NVDA.US",
    "last_done": "189.820",
    "change_rate": "0.70",
    "change_value": "1.320",
    "pe_ttm_ratio": "35.40",
    "pb_ratio": "28.12",
    "dividend_ratio_ttm": "0.03",
    "five_day_change_rate": "2.15",
    "ten_day_change_rate": "-1.32",
    "half_year_change_rate": "18.50"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `last_done` | string | 最新价 |
| `change_rate` | string | 今日涨跌幅（%） |
| `change_value` | string | 今日涨跌额 |
| `pe_ttm_ratio` | string | 市盈率 TTM |
| `pb_ratio` | string | 市净率 |
| `dividend_ratio_ttm` | string | 股息率 TTM（%） |
| `five_day_change_rate` | string | 5日涨跌幅（%） |
| `ten_day_change_rate` | string | 10日涨跌幅（%） |
| `half_year_change_rate` | string | 半年涨跌幅（%） |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/indexes?symbols=NVDA.US,AAPL.US"
```

---

### 资金分布

### `GET /api/capital/{symbol}`

获取大单/中单/小单资金流入流出分布。

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 股票代码 |

**响应**

```json
{
  "symbol": "700.HK",
  "capital_in": {
    "large":  "512340000.00",
    "medium": "234120000.00",
    "small":  "98760000.00"
  },
  "capital_out": {
    "large":  "389200000.00",
    "medium": "198430000.00",
    "small":  "112340000.00"
  },
  "timestamp": 1771621140
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `capital_in` | object | 资金流入，按大/中/小单分类（单位：原始货币） |
| `capital_out` | object | 资金流出，按大/中/小单分类 |
| `large` | string | 大单金额 |
| `medium` | string | 中单金额 |
| `small` | string | 小单金额 |
| `timestamp` | int | 数据时间（Unix 秒） |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/capital/700.HK"
```

---

## 资产接口

> 所有资产接口均基于 LongPort **交易账户**，返回真实（或模拟盘）持仓与资金数据。

### 账户余额

### `GET /api/assets/balance`

查询账户净资产、现金、保证金等信息。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `currency` | ❌ | 按货币筛选，如 `USD`、`HKD`；不传则返回全部 |

**响应** — `AccountBalance[]`

```json
[
  {
    "currency": "HKD",
    "net_assets": "930115.91",
    "total_cash": "-1241395.34",
    "buy_power": "94392.70",
    "init_margin": "835695.45",
    "maintenance_margin": "727676.74",
    "margin_call": "0",
    "risk_level": 1,
    "max_finance_amount": "3200000.00",
    "remaining_finance_amount": "1949566.82",
    "cash_infos": [
      {
        "currency": "USD",
        "available_cash": "-159825.77",
        "withdraw_cash": "-159825.77",
        "frozen_cash": "1156.25",
        "settling_cash": "1156.25"
      },
      {
        "currency": "HKD",
        "available_cash": "-4990.87",
        "withdraw_cash": "-4990.87",
        "frozen_cash": "27.76",
        "settling_cash": "0.00"
      }
    ]
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `currency` | string | 结算货币 |
| `net_assets` | string | 净资产 |
| `total_cash` | string | 现金总额（负值代表融资借款） |
| `buy_power` | string | 购买力 |
| `init_margin` | string | 初始保证金 |
| `maintenance_margin` | string | 维持保证金 |
| `margin_call` | string | 追保金额（0 表示无追保） |
| `risk_level` | int | 风险等级（1=低，数值越大风险越高） |
| `max_finance_amount` | string | 最大融资额度 |
| `remaining_finance_amount` | string | 剩余可用融资额度 |
| `cash_infos` | CashInfo[] | 各货币现金明细 |
| `cash_infos[].available_cash` | string | 可用现金 |
| `cash_infos[].withdraw_cash` | string | 可提现金 |
| `cash_infos[].frozen_cash` | string | 冻结现金 |
| `cash_infos[].settling_cash` | string | 在途结算现金 |

**示例**

```bash
# 全部货币
curl "${PUBLIC_BASE_URL}/api/assets/balance"

# 只看 USD
curl "${PUBLIC_BASE_URL}/api/assets/balance?currency=USD"
```

---

### 股票持仓

### `GET /api/assets/positions`

查询当前所有股票持仓，支持按标的筛选。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ❌ | 标的过滤，逗号分隔，如 `AAPL.US,700.HK` |

**响应** — `StockPosition[]`

```json
[
  {
    "account_channel": "lb_papertrading",
    "symbol": "AAPL.US",
    "symbol_name": "Apple",
    "market": "US",
    "currency": "USD",
    "quantity": 12,
    "available_quantity": 12,
    "init_quantity": 12,
    "cost_price": "202.230"
  },
  {
    "account_channel": "lb_papertrading",
    "symbol": "5.HK",
    "symbol_name": "HSBC HOLDINGS",
    "market": "HK",
    "currency": "HKD",
    "quantity": 2000,
    "available_quantity": 2000,
    "init_quantity": 2000,
    "cost_price": "96.950"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `account_channel` | string | 子账户标识 |
| `symbol` | string | 股票代码 |
| `symbol_name` | string | 股票名称 |
| `market` | string | 市场：`US` / `HK` / `CN` |
| `currency` | string | 交易货币 |
| `quantity` | int | 总持仓量（股） |
| `available_quantity` | int | 可交易数量（股，已扣除冻结部分） |
| `init_quantity` | int\|null | 当日开盘前持仓量（日内交易参考） |
| `cost_price` | string | 成本价 |

**示例**

```bash
# 全部持仓
curl "${PUBLIC_BASE_URL}/api/assets/positions"

# 查询指定持仓
curl "${PUBLIC_BASE_URL}/api/assets/positions?symbols=AAPL.US,MSFT.US"
```

---

### 基金持仓

### `GET /api/assets/fund_positions`

查询基金（公募/ETF申购）持仓，未持有基金时返回空数组。

**Query 参数**

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbols` | ❌ | 基金代码过滤，逗号分隔 |

**响应** — `FundPosition[]`

```json
[
  {
    "account_channel": "lb_papertrading",
    "symbol": "HK_FUND_001",
    "symbol_name": "某某基金",
    "currency": "HKD",
    "holding_units": "1000.00",
    "current_net_asset_value": "1.2345",
    "cost_net_asset_value": "1.1800",
    "net_asset_value_day": "2026-02-21"
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `holding_units` | string | 持有份额 |
| `current_net_asset_value` | string | 最新单位净值 |
| `cost_net_asset_value` | string | 成本单位净值 |
| `net_asset_value_day` | string | 净值日期 |

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/assets/fund_positions"
```

---

## 自选股接口

自选股持久化存储于服务器本地文件（`~/.jiang_equity_request_watchlist.json`）。

### 获取自选股

### `GET /api/watchlist`

**响应**

```json
{ "symbols": ["700.HK", "AAPL.US", "NVDA.US"] }
```

**示例**

```bash
curl "${PUBLIC_BASE_URL}/api/watchlist"
```

---

### 添加自选股

### `POST /api/watchlist`

**请求体**

```json
{ "symbol": "TSLA.US" }
```

**响应**

```json
{ "symbols": ["700.HK", "AAPL.US", "NVDA.US", "TSLA.US"] }
```

**示例**

```bash
curl -X POST "${PUBLIC_BASE_URL}/api/watchlist" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TSLA.US"}'
```

---

### 删除自选股

### `DELETE /api/watchlist/{symbol}`

**路径参数**

| 参数 | 说明 |
|------|------|
| `symbol` | 要删除的股票代码 |

**响应**

```json
{ "symbols": ["700.HK", "AAPL.US", "NVDA.US"] }
```

**错误响应**（404）：标的不在自选股中

```json
{ "detail": "TSLA.US 不在自选股中" }
```

**示例**

```bash
curl -X DELETE "${PUBLIC_BASE_URL}/api/watchlist/TSLA.US"
```

---

## WebSocket 实时推送

### 连接地址

```
${WS_BASE_URL}/ws/quotes
```

### 客户端 → 服务端

建立连接后，发送 JSON 消息控制订阅：

**订阅**

```json
{ "action": "subscribe", "symbols": ["700.HK", "AAPL.US"] }
```

**取消订阅**

```json
{ "action": "unsubscribe", "symbols": ["700.HK"] }
```

### 服务端 → 客户端

**订阅确认（ack）**

```json
{
  "type": "ack",
  "action": "subscribe",
  "symbols": ["700.HK"],
  "subscribed": ["700.HK", "AAPL.US"]
}
```

**实时行情推送（quote）**

```json
{
  "type": "quote",
  "symbol": "700.HK",
  "data": {
    "last_done": "385.40",
    "open": "380.00",
    "high": "387.00",
    "low": "379.50",
    "volume": 12345678,
    "turnover": "4738291234.00",
    "change": "5.40",
    "change_pct": "1.42",
    "timestamp": 1771621140,
    "is_up": true
  }
}
```

**K 线推送（candlestick）**

```json
{
  "type": "candlestick",
  "symbol": "AAPL.US",
  "data": {
    "period": "Period.Day",
    "open": "188.50",
    "close": "189.82",
    "high": "190.10",
    "low": "187.80",
    "volume": 45231890,
    "turnover": "8534912345.00",
    "timestamp": 1771621140
  }
}
```

**实时逐笔成交推送（trades）**

```json
{
  "type": "trades",
  "symbol": "700.HK",
  "data": {
    "trades": [
      {
        "price": "385.60",
        "volume": 500,
        "timestamp": 1771621145,
        "direction": "Up",
        "trade_type": "REGULAR",
        "trade_session": "NormalTrade"
      }
    ]
  }
}
```

> `direction` 取值：`Up`（主动买）、`Down`（主动卖）、`Neutral`。

**实时盘口深度推送（depth）**

```json
{
  "type": "depth",
  "symbol": "700.HK",
  "data": {
    "asks": [
      {"price": "385.80", "volume": 3000, "order_num": 5},
      {"price": "386.00", "volume": 1200, "order_num": 2}
    ],
    "bids": [
      {"price": "385.60", "volume": 4500, "order_num": 8},
      {"price": "385.40", "volume": 2100, "order_num": 3}
    ]
  }
}
```

**错误消息**

```json
{ "type": "error", "message": "未知 action: foo" }
```

### WebSocket 快速测试（wscat）

```bash
npm install -g wscat
wscat -c ${WS_BASE_URL}/ws/quotes

# 连接后发送：
{"action":"subscribe","symbols":["700.HK","AAPL.US"]}
```

---

## 市场日历接口

### `GET /api/market/sessions`

返回所有市场的交易时段信息（开盘时间、收盘时间、盘前/盘后）。

**请求参数**：无

**响应**

```json
[
  {
    "market": "HK",
    "trade_sessions": [
      {"begin_time": "09:30", "end_time": "12:00", "trade_session": "NormalTrade"},
      {"begin_time": "13:00", "end_time": "16:00", "trade_session": "NormalTrade"}
    ]
  },
  {
    "market": "US",
    "trade_sessions": [
      {"begin_time": "04:00", "end_time": "09:30", "trade_session": "PreMarketTrade"},
      {"begin_time": "09:30", "end_time": "16:00", "trade_session": "NormalTrade"},
      {"begin_time": "16:00", "end_time": "20:00", "trade_session": "PostMarketTrade"}
    ]
  }
]
```

**响应字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `market` | string | 市场代码：`HK` / `US` / `CN` / `SG` / `Crypto` |
| `trade_sessions` | object[] | 该市场的各交易时段列表 |
| `trade_sessions[].begin_time` | string | 时段开始时间（`HH:MM`，当地时间） |
| `trade_sessions[].end_time` | string | 时段结束时间（`HH:MM`，当地时间） |
| `trade_sessions[].trade_session` | string | 时段类型，见下表 |

**`trade_session` 枚举值**

| 值 | 说明 |
|----|------|
| `NormalTrade` | 正常交易时段 |
| `PreMarketTrade` | 盘前交易（美股） |
| `PostMarketTrade` | 盘后交易（美股） |
| `OvernightTrade` | 夜盘（部分市场） |

**示例**

```bash
curl ${PUBLIC_BASE_URL}/api/market/sessions
```

---

### `GET /api/market/trading_days`

返回指定市场、日期范围内的交易日和半交易日（如港股特别收市）列表。

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `market` | string | 否 | `HK` | 市场代码：`HK` / `US` / `CN` / `SG` / `Crypto` |
| `begin` | string | 否 | 今天 -30 天 | 开始日期，格式 `YYYY-MM-DD` |
| `end` | string | 否 | 今天 | 结束日期，格式 `YYYY-MM-DD` |

> 日期范围不能超过 **365 天**（SDK 限制）。

**响应**

```json
{
  "market": "HK",
  "begin": "2025-02-01",
  "end": "2025-02-21",
  "trading_days": [
    "2025-02-03",
    "2025-02-04",
    "2025-02-05",
    "2025-02-06",
    "2025-02-07"
  ],
  "half_trading_days": [
    "2025-01-29"
  ]
}
```

**响应字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| `market` | string | 市场代码 |
| `begin` | string | 查询开始日期（`YYYY-MM-DD`） |
| `end` | string | 查询结束日期（`YYYY-MM-DD`） |
| `trading_days` | string[] | 正常交易日列表 |
| `half_trading_days` | string[] | 半交易日列表（如港股提前收市日） |

**示例**

```bash
# 查询港股近 30 天交易日（默认）
curl "${PUBLIC_BASE_URL}/api/market/trading_days"

# 查询美股 2025 年 1 月交易日
curl "${PUBLIC_BASE_URL}/api/market/trading_days?market=US&begin=2025-01-01&end=2025-01-31"

# 查询 A 股交易日
curl "${PUBLIC_BASE_URL}/api/market/trading_days?market=CN&begin=2025-02-01&end=2025-02-28"
```

---

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| `200` | 成功 |
| `400` | 请求参数有误（如 `symbols` 为空） |
| `404` | 资源不存在（如自选股中无此标的） |
| `500` | 服务器内部错误（详细错误写入服务端日志，客户端返回通用信息） |

---

## 股票代码格式

| 市场 | 格式 | 示例 |
|------|------|------|
| 美股 | `{代码}.US` | `AAPL.US`、`NVDA.US`、`TSLA.US` |
| 港股 | `{代码}.HK` | `700.HK`、`9988.HK` |
| A股 | `{代码}.SH` / `{代码}.SZ` | `600519.SH`、`000858.SZ` |
