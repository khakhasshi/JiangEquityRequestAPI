"""
基本面相关 REST 路由。

端点：
  GET /api/fundamental?symbols=700.HK,AAPL.US   静态信息 + 估值指标合并返回
  GET /api/static?symbols=700.HK,AAPL.US        纯静态信息（名称/股本/EPS/BPS/股息率）
  GET /api/indexes?symbols=700.HK,AAPL.US       估值/涨跌指标（PE/PB/各周期涨跌幅）
  GET /api/capital/{symbol}                      资金分布（大/中/小单 流入流出）
"""
import logging

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api", tags=["fundamental"])
logger = logging.getLogger(__name__)


def _svc(request: Request):
    return request.app.state.quote_service


@router.get("/fundamental")
async def get_fundamental(symbols: str, request: Request):
    """
    合并返回静态信息 + 估值指标，按 symbol 对齐。
    示例: GET /api/fundamental?symbols=700.HK,AAPL.US
    """
    svc = _svc(request)
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols 参数不能为空")
    try:
        static  = await svc.get_static_info(symbol_list)
        indexes = await svc.get_calc_indexes(symbol_list)
        # 以 symbol 为 key 合并
        index_map = {item["symbol"]: item for item in indexes}
        result = []
        for s in static:
            sym = s["symbol"]
            merged = {**s, **index_map.get(sym, {})}
            result.append(merged)
        return result
    except Exception as e:
        logger.exception("get_fundamental failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/static")
async def get_static_info(symbols: str, request: Request):
    """
    静态基本面：名称、交易所、货币、股本、EPS、BPS、股息率等。
    示例: GET /api/static?symbols=700.HK,AAPL.US
    """
    svc = _svc(request)
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols 参数不能为空")
    try:
        return await svc.get_static_info(symbol_list)
    except Exception as e:
        logger.exception("get_static_info failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/indexes")
async def get_calc_indexes(symbols: str, request: Request):
    """
    估值 & 涨跌指标：PE-TTM、PB、股息率 TTM、5/10/半年涨跌幅、总市值、换手率等。
    示例: GET /api/indexes?symbols=700.HK,AAPL.US
    """
    svc = _svc(request)
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols 参数不能为空")
    try:
        return await svc.get_calc_indexes(symbol_list)
    except Exception as e:
        logger.exception("get_calc_indexes failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/capital/{symbol:path}")
async def get_capital_distribution(symbol: str, request: Request):
    """
    资金分布：大单 / 中单 / 小单 各自的流入与流出金额。
    示例: GET /api/capital/700.HK
    """
    svc = _svc(request)
    try:
        return await svc.get_capital_distribution(symbol)
    except Exception as e:
        logger.exception("get_capital_distribution failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")
