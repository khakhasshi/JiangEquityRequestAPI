import asyncio
import logging
import os
from decimal import Decimal
from typing import Callable, Awaitable

from longport.openapi import (
    Config,
    AsyncQuoteContext,
    SubType,
    AdjustType,
    Period,
    PushQuote,
    PushCandlestick,
    PushTrades,
    PushDepth,
    PushBrokers,
    CalcIndex,
    Market,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 将 LongPort Period 字符串映射到 SDK 枚举
# --------------------------------------------------------------------------- #
PERIOD_MAP: dict[str, Period] = {
    "1min":  Period.Min_1,
    "5min":  Period.Min_5,
    "15min": Period.Min_15,
    "30min": Period.Min_30,
    "60min": Period.Min_60,
    "day":   Period.Day,
    "week":  Period.Week,
    "month": Period.Month,
    "year":  Period.Year,
}


def _decimal_to_str(v) -> str:
    """将 Decimal / float / str 统一序列化为字符串，避免精度损失。"""
    if v is None:
        return "0"
    return str(v)


def _quote_to_dict(symbol: str, q) -> dict:
    """把 QuoteContext.quote() 返回的单条记录转成可序列化字典。"""
    prev_close = getattr(q, "prev_close", None) or getattr(q, "last_close", None)
    last_done = getattr(q, "last_done", None) or getattr(q, "cur_price", None) or Decimal("0")
    open_price = getattr(q, "open", Decimal("0"))
    high = getattr(q, "high", Decimal("0"))
    low = getattr(q, "low", Decimal("0"))
    volume = getattr(q, "volume", 0)
    turnover = getattr(q, "turnover", Decimal("0"))
    timestamp = getattr(q, "timestamp", None)

    change = last_done - (prev_close or last_done)
    change_pct = (change / prev_close * 100) if (prev_close and prev_close != 0) else Decimal("0")

    return {
        "symbol":     symbol,
        "name":       getattr(q, "symbol", symbol),
        "last_done":  _decimal_to_str(last_done),
        "open":       _decimal_to_str(open_price),
        "high":       _decimal_to_str(high),
        "low":        _decimal_to_str(low),
        "prev_close": _decimal_to_str(prev_close),
        "volume":     int(volume),
        "turnover":   _decimal_to_str(turnover),
        "change":     _decimal_to_str(change),
        "change_pct": _decimal_to_str(change_pct.quantize(Decimal("0.01")) if isinstance(change_pct, Decimal) else round(float(change_pct), 2)),
        "timestamp":  int(timestamp.timestamp()) if hasattr(timestamp, "timestamp") else (int(timestamp) if timestamp else 0),
        "is_up":      float(str(change)) >= 0,
    }


def _push_quote_to_dict(event: PushQuote) -> dict:
    last_done = getattr(event, "last_done", Decimal("0"))
    open_price = getattr(event, "open", Decimal("0"))
    high = getattr(event, "high", Decimal("0"))
    low = getattr(event, "low", Decimal("0"))
    volume = getattr(event, "volume", 0)
    turnover = getattr(event, "turnover", Decimal("0"))
    change = getattr(event, "change", Decimal("0"))
    change_rate = getattr(event, "change_rate", Decimal("0"))
    timestamp = getattr(event, "timestamp", None)

    return {
        "last_done":  _decimal_to_str(last_done),
        "open":       _decimal_to_str(open_price),
        "high":       _decimal_to_str(high),
        "low":        _decimal_to_str(low),
        "volume":     int(volume),
        "turnover":   _decimal_to_str(turnover),
        "change":     _decimal_to_str(change),
        "change_pct": _decimal_to_str(change_rate),
        "timestamp":  int(timestamp.timestamp()) if hasattr(timestamp, "timestamp") else (int(timestamp) if timestamp else 0),
        "is_up":      float(str(change)) >= 0,
    }


def _push_candlestick_to_dict(event: PushCandlestick) -> dict:
    candle = getattr(event, "candlestick", None) or event
    timestamp = getattr(candle, "timestamp", None)
    return {
        "period":    str(getattr(event, "period", "")),
        "open":      _decimal_to_str(getattr(candle, "open", 0)),
        "close":     _decimal_to_str(getattr(candle, "close", 0)),
        "high":      _decimal_to_str(getattr(candle, "high", 0)),
        "low":       _decimal_to_str(getattr(candle, "low", 0)),
        "volume":    int(getattr(candle, "volume", 0)),
        "turnover":  _decimal_to_str(getattr(candle, "turnover", 0)),
        "timestamp": int(timestamp.timestamp()) if hasattr(timestamp, "timestamp") else (int(timestamp) if timestamp else 0),
    }


def _push_trades_to_dict(event: PushTrades) -> dict:
    """序列化实时逐笔成交推送。"""
    trades_list = []
    for t in (getattr(event, "trades", []) or []):
        ts = getattr(t, "timestamp", None)
        direction = getattr(t, "direction", None)
        trades_list.append({
            "price":         _decimal_to_str(getattr(t, "price", 0)),
            "volume":        int(getattr(t, "volume", 0)),
            "timestamp":     int(ts.timestamp()) if hasattr(ts, "timestamp") else (int(ts) if ts else 0),
            "direction":     str(direction).split(".")[-1] if direction else "",
            "trade_type":    str(getattr(t, "trade_type", "")),
            "trade_session": str(getattr(t, "trade_session", "")),
        })
    return {"trades": trades_list}


def _push_depth_to_dict(event: PushDepth) -> dict:
    """序列化实时盘口深度推送。"""
    def _level(lv) -> dict:
        return {
            "price":     _decimal_to_str(getattr(lv, "price", 0)),
            "volume":    int(getattr(lv, "volume", 0)),
            "order_num": int(getattr(lv, "order_num", 0)),
        }
    asks = [_level(lv) for lv in (getattr(event, "asks", []) or [])]
    bids = [_level(lv) for lv in (getattr(event, "bids", []) or [])]
    return {"asks": asks, "bids": bids}


# --------------------------------------------------------------------------- #
# QuoteService
# --------------------------------------------------------------------------- #
PushCallback = Callable[[str, str, dict], Awaitable[None]]


class QuoteService:
    """封装 LongPort AsyncQuoteContext，提供行情查询与实时推送。"""

    def __init__(self, push_callback: PushCallback):
        self._push_callback = push_callback
        self._ctx: AsyncQuoteContext | None = None
        self._subscribed: set[str] = set()

    async def start(self):
        """初始化 LongPort 连接。Config 从环境变量读取（config.py 已在 main.py 中提前注入）。"""
        config = Config.from_env()
        self._ctx = await AsyncQuoteContext.create(config)
        self._ctx.set_on_quote(self._on_quote)
        self._ctx.set_on_candlestick(self._on_candlestick)
        self._ctx.set_on_trades(self._on_trades)
        self._ctx.set_on_depth(self._on_depth)
        logger.info("LongPort QuoteContext initialized (quote/candlestick/trades/depth).")

    # ------------------------------------------------------------------ #
    # 推送回调（由 SDK 内部线程调用，用 asyncio.create_task 转入事件循环）
    # ------------------------------------------------------------------ #
    def _on_quote(self, symbol: str, event: PushQuote):
        data = _push_quote_to_dict(event)
        asyncio.create_task(self._push_callback("quote", symbol, data))

    def _on_candlestick(self, symbol: str, event: PushCandlestick):
        data = _push_candlestick_to_dict(event)
        asyncio.create_task(self._push_callback("candlestick", symbol, data))

    def _on_trades(self, symbol: str, event: PushTrades):
        data = _push_trades_to_dict(event)
        asyncio.create_task(self._push_callback("trades", symbol, data))

    def _on_depth(self, symbol: str, event: PushDepth):
        data = _push_depth_to_dict(event)
        asyncio.create_task(self._push_callback("depth", symbol, data))

    # ------------------------------------------------------------------ #
    # 公开接口
    # ------------------------------------------------------------------ #
    async def subscribe(self, symbols: list[str]):
        new = [s for s in symbols if s not in self._subscribed]
        if new:
            # 订阅实时报价 + 逐笔成交 + 盘口深度
            await self._ctx.subscribe(new, [SubType.Quote, SubType.Trade, SubType.Depth])
            # 逐只订阅日K线推送
            for sym in new:
                try:
                    await self._ctx.subscribe_candlesticks(sym, Period.Day)
                except Exception as e:
                    logger.warning(f"subscribe_candlesticks({sym}) failed: {e}")
            self._subscribed.update(new)
            logger.info(f"Subscribed: {new}")

    async def unsubscribe(self, symbols: list[str]):
        existing = [s for s in symbols if s in self._subscribed]
        if existing:
            await self._ctx.unsubscribe(existing, [SubType.Quote, SubType.Trade, SubType.Depth])
            for sym in existing:
                try:
                    await self._ctx.unsubscribe_candlesticks(sym, Period.Day)
                except Exception as e:
                    logger.warning(f"unsubscribe_candlesticks({sym}) failed: {e}")
            self._subscribed.difference_update(existing)
            logger.info(f"Unsubscribed: {existing}")

    async def get_quotes(self, symbols: list[str]) -> list[dict]:
        items = await self._ctx.quote(symbols)
        result = []
        for i, item in enumerate(items):
            sym = symbols[i] if i < len(symbols) else getattr(item, "symbol", "")
            result.append(_quote_to_dict(sym, item))
        return result

    async def get_candlesticks(self, symbol: str, period_str: str = "day", count: int = 90) -> list[dict]:
        period = PERIOD_MAP.get(period_str, Period.Day)
        items = await self._ctx.history_candlesticks_by_offset(
            symbol, period, AdjustType.NoAdjust, False, count
        )
        result = []
        for item in items:
            timestamp = getattr(item, "timestamp", None)
            result.append({
                "timestamp": int(timestamp.timestamp()) if hasattr(timestamp, "timestamp") else (int(timestamp) if timestamp else 0),
                "open":     _decimal_to_str(getattr(item, "open", 0)),
                "close":    _decimal_to_str(getattr(item, "close", 0)),
                "high":     _decimal_to_str(getattr(item, "high", 0)),
                "low":      _decimal_to_str(getattr(item, "low", 0)),
                "volume":   int(getattr(item, "volume", 0)),
                "turnover": _decimal_to_str(getattr(item, "turnover", 0)),
            })
        return result

    async def get_candlesticks_by_date(
        self,
        symbol: str,
        period_str: str = "day",
        start=None,
        end=None,
        adjust: str = "none",
    ) -> list[dict]:
        """
        按时间段查询历史 K 线。
        官方签名（位置参数）:
          history_candlesticks_by_date(symbol, period, adjust_type, start, end)
        start / end: datetime.date 或 datetime.datetime（取 date 部分传给 SDK）
        """
        import datetime as _dt
        period = PERIOD_MAP.get(period_str, Period.Day)
        adjust_map = {
            "none":    AdjustType.NoAdjust,
            "forward": AdjustType.ForwardAdjust,
        }
        adj = adjust_map.get((adjust or "none").lower(), AdjustType.NoAdjust)

        def _to_date(v):
            if v is None:
                return None
            if isinstance(v, _dt.datetime):
                return v.date()
            if isinstance(v, _dt.date):
                return v
            return None

        # 官方示例：ctx.history_candlesticks_by_date("700.HK", Period.Day, AdjustType.NoAdjust, date(2023,1,1), date(2023,2,1))
        items = await self._ctx.history_candlesticks_by_date(
            symbol, period, adj, _to_date(start), _to_date(end)
        )

        result = []
        for item in items:
            timestamp = getattr(item, "timestamp", None)
            ts_int = int(timestamp.timestamp()) if hasattr(timestamp, "timestamp") else (int(timestamp) if timestamp else 0)
            result.append({
                "timestamp": ts_int,
                "open":     _decimal_to_str(getattr(item, "open", 0)),
                "close":    _decimal_to_str(getattr(item, "close", 0)),
                "high":     _decimal_to_str(getattr(item, "high", 0)),
                "low":      _decimal_to_str(getattr(item, "low", 0)),
                "volume":   int(getattr(item, "volume", 0)),
                "turnover": _decimal_to_str(getattr(item, "turnover", 0)),
            })
        return result

    async def get_trades(self, symbol: str, count: int = 100) -> list[dict]:
        """逐笔成交：最近 count 笔成交记录。"""
        items = await self._ctx.trades(symbol, count)
        result = []
        for item in items:
            ts = getattr(item, "timestamp", None)
            direction = getattr(item, "direction", None)
            result.append({
                "price":         _decimal_to_str(getattr(item, "price", 0)),
                "volume":        int(getattr(item, "volume", 0)),
                "timestamp":     int(ts.timestamp()) if hasattr(ts, "timestamp") else (int(ts) if ts else 0),
                "direction":     str(direction).split(".")[-1] if direction else "",  # "Up" / "Down" / "Neutral"
                "trade_type":    str(getattr(item, "trade_type", "")),
                "trade_session": str(getattr(item, "trade_session", "")).split(".")[-1],
            })
        return result

    async def get_intraday(self, symbol: str) -> list[dict]:
        """分时数据：当日每分钟的价格、均价、成交量、成交额。"""
        items = await self._ctx.intraday(symbol)
        result = []
        for item in items:
            ts = getattr(item, "timestamp", None)
            result.append({
                "timestamp": int(ts.timestamp()) if hasattr(ts, "timestamp") else (int(ts) if ts else 0),
                "price":     _decimal_to_str(getattr(item, "price", 0)),
                "avg_price": _decimal_to_str(getattr(item, "avg_price", 0)),
                "volume":    int(getattr(item, "volume", 0)),
                "turnover":  _decimal_to_str(getattr(item, "turnover", 0)),
            })
        return result

    async def get_depth(self, symbol: str) -> dict:
        resp = await self._ctx.depth(symbol)

        def _level(lv) -> dict:
            return {
                "price":     _decimal_to_str(getattr(lv, "price", 0)),
                "volume":    int(getattr(lv, "volume", 0)),
                "order_num": int(getattr(lv, "order_num", 0)),
            }

        asks = [_level(lv) for lv in (getattr(resp, "asks", []) or [])]
        bids = [_level(lv) for lv in (getattr(resp, "bids", []) or [])]
        return {"symbol": symbol, "asks": asks, "bids": bids}

    @property
    def subscribed_symbols(self) -> list[str]:
        return list(self._subscribed)

    # ------------------------------------------------------------------ #
    # 基本面
    # ------------------------------------------------------------------ #

    async def get_static_info(self, symbols: list[str]) -> list[dict]:
        """静态基本面：名称、交易所、流通股、EPS、BPS、股息率等。"""
        items = await self._ctx.static_info(symbols)
        result = []
        for item in items:
            derivatives = [
                str(d) for d in (getattr(item, "stock_derivatives", []) or [])
            ]
            result.append({
                "symbol":             getattr(item, "symbol", ""),
                "name_cn":            getattr(item, "name_cn", ""),
                "name_en":            getattr(item, "name_en", ""),
                "name_hk":            getattr(item, "name_hk", ""),
                "exchange":           getattr(item, "exchange", ""),
                "currency":           getattr(item, "currency", ""),
                "lot_size":           int(getattr(item, "lot_size", 0) or 0),
                "total_shares":       int(getattr(item, "total_shares", 0) or 0),
                "circulating_shares": int(getattr(item, "circulating_shares", 0) or 0),
                "hk_shares":          int(getattr(item, "hk_shares", 0) or 0),
                "eps":                _decimal_to_str(getattr(item, "eps", None)),
                "eps_ttm":            _decimal_to_str(getattr(item, "eps_ttm", None)),
                "bps":                _decimal_to_str(getattr(item, "bps", None)),
                "dividend_yield":     _decimal_to_str(getattr(item, "dividend_yield", None)),
                "stock_derivatives":  derivatives,
            })
        return result

    async def get_calc_indexes(self, symbols: list[str]) -> list[dict]:
        """估值指标：PE、PB、股息率 TTM、各周期涨跌幅、总市值、换手率等。"""
        indexes = [
            CalcIndex.LastDone,
            CalcIndex.ChangeRate,
            CalcIndex.ChangeValue,
            CalcIndex.PeTtmRatio,
            CalcIndex.PbRatio,
            CalcIndex.DividendRatioTtm,
            CalcIndex.FiveDayChangeRate,
            CalcIndex.TenDayChangeRate,
            CalcIndex.HalfYearChangeRate,
        ]
        items = await self._ctx.calc_indexes(symbols, indexes)
        result = []
        for item in items:
            result.append({
                "symbol":              getattr(item, "symbol", ""),
                "last_done":           _decimal_to_str(getattr(item, "last_done", None)),
                "change_rate":         _decimal_to_str(getattr(item, "change_rate", None)),
                "change_value":        _decimal_to_str(getattr(item, "change_value", None)),
                "pe_ttm_ratio":        _decimal_to_str(getattr(item, "pe_ttm_ratio", None)),
                "pb_ratio":            _decimal_to_str(getattr(item, "pb_ratio", None)),
                "dividend_ratio_ttm":  _decimal_to_str(getattr(item, "dividend_ratio_ttm", None)),
                "five_day_change_rate":     _decimal_to_str(getattr(item, "five_day_change_rate", None)),
                "ten_day_change_rate":      _decimal_to_str(getattr(item, "ten_day_change_rate", None)),
                "half_year_change_rate":    _decimal_to_str(getattr(item, "half_year_change_rate", None)),
            })
        return result

    async def get_capital_distribution(self, symbol: str) -> dict:
        """资金分布：大单/中单/小单 流入/流出。"""
        resp = await self._ctx.capital_distribution(symbol)

        def _side(obj) -> dict:
            return {
                "large":  _decimal_to_str(getattr(obj, "large", None)),
                "medium": _decimal_to_str(getattr(obj, "medium", None)),
                "small":  _decimal_to_str(getattr(obj, "small", None)),
            }

        ts = getattr(resp, "timestamp", None)
        return {
            "symbol":      symbol,
            "capital_in":  _side(getattr(resp, "capital_in", None) or object()),
            "capital_out": _side(getattr(resp, "capital_out", None) or object()),
            "timestamp":   int(ts.timestamp()) if hasattr(ts, "timestamp") else (int(ts) if ts else 0),
        }

    # ----------------------------------------------------------------------- #
    # 市场日历 & 交易时段
    # ----------------------------------------------------------------------- #

    # 字符串 → Market 枚举
    _MARKET_MAP: dict = {
        "HK":     None,  # 填充于类加载后
        "US":     None,
        "CN":     None,
        "SG":     None,
        "Crypto": None,
    }

    async def get_trading_session(self) -> list:
        """
        返回所有市场的交易时段信息。
        每项格式:
          {
            "market": "HK",
            "trade_sessions": [
              {"begin_time": "09:30", "end_time": "12:00", "trade_session": "NormalTrade"},
              ...
            ]
          }
        """
        items = await self._ctx.trading_session()
        result = []
        for item in items:
            market_val = getattr(item, "market", None)
            market_str = str(market_val).replace("Market.", "") if market_val is not None else ""
            sessions = []
            for ts in getattr(item, "trade_sessions", []):
                begin = getattr(ts, "begin_time", None)
                end   = getattr(ts, "end_time", None)
                session_type = getattr(ts, "trade_session", None)
                sessions.append({
                    "begin_time":    begin.strftime("%H:%M") if hasattr(begin, "strftime") else str(begin),
                    "end_time":      end.strftime("%H:%M") if hasattr(end, "strftime") else str(end),
                    "trade_session": str(session_type).replace("TradeSession.", "") if session_type is not None else "",
                })
            result.append({
                "market":         market_str,
                "trade_sessions": sessions,
            })
        return result

    async def get_trading_days(
        self,
        market: str,
        begin: "datetime.date",
        end: "datetime.date",
    ) -> dict:
        """
        返回指定市场、日期范围内的交易日和半日市信息。
        market: HK / US / CN / SG / Crypto
        """
        import datetime as _dt
        market_map = {
            "HK":     Market.HK,
            "US":     Market.US,
            "CN":     Market.CN,
            "SG":     Market.SG,
            "Crypto": Market.Crypto,
        }
        mkt = market_map.get(market.upper() if market else "", Market.HK)
        resp = await self._ctx.trading_days(mkt, begin, end)
        def _fmt(d) -> str:
            return d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
        return {
            "market":             market.upper(),
            "begin":              _fmt(begin),
            "end":                _fmt(end),
            "trading_days":       [_fmt(d) for d in getattr(resp, "trading_days", [])],
            "half_trading_days":  [_fmt(d) for d in getattr(resp, "half_trading_days", [])],
        }
