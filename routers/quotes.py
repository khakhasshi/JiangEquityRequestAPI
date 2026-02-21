"""
行情相关 REST 路由。
通过 FastAPI dependency 获取 QuoteService 实例（注入自 main.py 的 app.state）。
"""
import logging

from fastapi import APIRouter, HTTPException, Request

from models import SubscribeRequest

router = APIRouter(prefix="/api", tags=["quotes"])
logger = logging.getLogger(__name__)


def get_quote_service(request: Request):
    return request.app.state.quote_service


@router.get("/quotes")
async def get_quotes(symbols: str, request: Request):
    """
    批量获取行情快照。
    示例: GET /api/quotes?symbols=700.HK,AAPL.US
    """
    svc = get_quote_service(request)
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols 参数不能为空")
    try:
        return await svc.get_quotes(symbol_list)
    except Exception as e:
        logger.exception("get_quotes failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/quote/{symbol:path}")
async def get_quote(symbol: str, request: Request):
    """获取单只股票行情快照。"""
    svc = get_quote_service(request)
    try:
        result = await svc.get_quotes([symbol])
        if not result:
            raise HTTPException(status_code=404, detail=f"{symbol} 未找到")
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_quote failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/candlesticks/{symbol:path}")
async def get_candlesticks(
    symbol: str,
    request: Request,
    period: str = "day",
    count: int = 90,
):
    """
    获取历史 K 线（最近 count 根）。
    period: 1min / 5min / 15min / 30min / 60min / day / week / month / year
    count:  返回条数，默认 90
    """
    svc = get_quote_service(request)
    try:
        return await svc.get_candlesticks(symbol, period, count)
    except Exception as e:
        logger.exception("get_candlesticks failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/candlesticks_range/{symbol:path}")
async def get_candlesticks_range(
    symbol: str,
    request: Request,
    period: str = "day",
    start: str = None,
    end: str = None,
    adjust: str = "none",
):
    """
    获取指定日期范围内的全部 K 线。
    period: 1min / 5min / 15min / 30min / 60min / day / week / month / year
    start:  YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS（注：只取日期部分传给 SDK）
    end:    同上
    adjust: none（不复权）/ forward（前复权）
    """
    import datetime
    svc = get_quote_service(request)

    VALID_PERIODS = {"1min", "5min", "15min", "30min", "60min", "day", "week", "month", "year"}
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period 无效，可选: {', '.join(sorted(VALID_PERIODS))}")

    def _parse_dt(s: str):
        if not s:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise HTTPException(status_code=400, detail=f"日期格式错误: '{s}'，支持 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS")

    start_dt = _parse_dt(start)
    end_dt   = _parse_dt(end)
    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(status_code=400, detail="start 不能晚于 end")

    try:
        return await svc.get_candlesticks_by_date(symbol, period, start_dt, end_dt, adjust)
    except Exception as e:
        logger.exception("get_candlesticks_range failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/trades/{symbol:path}")
async def get_trades(
    symbol: str,
    request: Request,
    count: int = 100,
):
    """
    逐笔成交记录（最近 count 笔，最大 1000）。
    示例: GET /api/trades/NVDA.US?count=200
    """
    svc = get_quote_service(request)
    count = min(max(count, 1), 1000)
    try:
        return await svc.get_trades(symbol, count)
    except Exception as e:
        logger.exception("get_trades failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/intraday/{symbol:path}")
async def get_intraday(symbol: str, request: Request):
    """
    当日分时数据（每分钟价格、均价、成交量、成交额）。
    示例: GET /api/intraday/NVDA.US
    """
    svc = get_quote_service(request)
    try:
        return await svc.get_intraday(symbol)
    except Exception as e:
        logger.exception("get_intraday failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/depth/{symbol:path}")
async def get_depth(symbol: str, request: Request):
    """获取盘口十档数据。"""
    svc = get_quote_service(request)
    try:
        return await svc.get_depth(symbol)
    except Exception as e:
        logger.exception("get_depth failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.post("/subscribe")
async def subscribe(body: SubscribeRequest, request: Request):
    """订阅实时推送。"""
    svc = get_quote_service(request)
    try:
        await svc.subscribe(body.symbols)
        return {"subscribed": svc.subscribed_symbols}
    except Exception as e:
        logger.exception("subscribe failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.delete("/subscribe/{symbol:path}")
async def unsubscribe(symbol: str, request: Request):
    """取消订阅。"""
    svc = get_quote_service(request)
    try:
        await svc.unsubscribe([symbol])
        return {"subscribed": svc.subscribed_symbols}
    except Exception as e:
        logger.exception("unsubscribe failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")
