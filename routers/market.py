"""
市场日历相关 REST 路由。
- GET /api/market/sessions         — 所有市场交易时段
- GET /api/market/trading_days     — 指定市场交易日/半交易日列表
"""
import datetime
import logging

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/market", tags=["market"])
logger = logging.getLogger(__name__)


def _quote_service(request: Request):
    return request.app.state.quote_service


@router.get("/sessions")
async def get_trading_sessions(request: Request):
    """
    返回所有市场的交易时段信息。

    响应示例:
    ```json
    [
      {
        "market": "HK",
        "trade_sessions": [
          {"begin_time": "09:30", "end_time": "12:00", "trade_session": "NormalTrade"},
          {"begin_time": "13:00", "end_time": "16:00", "trade_session": "NormalTrade"}
        ]
      },
      ...
    ]
    ```
    """
    svc = _quote_service(request)
    try:
        return await svc.get_trading_session()
    except Exception as e:
        logger.exception("get_trading_sessions failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/trading_days")
async def get_trading_days(
    request: Request,
    market: str = Query("HK", description="市场代码: HK / US / CN / SG / Crypto"),
    begin: str  = Query(None, description="开始日期 YYYY-MM-DD，默认今天往前 30 天"),
    end:   str  = Query(None, description="结束日期 YYYY-MM-DD，默认今天"),
):
    """
    返回指定市场、日期范围内的交易日和半交易日列表。

    - **market**: HK / US / CN / SG / Crypto
    - **begin**:  YYYY-MM-DD，最早可查 1 年前（SDK 限制）
    - **end**:    YYYY-MM-DD

    响应示例:
    ```json
    {
      "market": "HK",
      "begin": "2025-02-01",
      "end":   "2025-02-21",
      "trading_days":      ["2025-02-03", "2025-02-04", ...],
      "half_trading_days": ["2025-01-29"]
    }
    ```
    """
    svc = _quote_service(request)

    # 允许的市场
    valid_markets = {"HK", "US", "CN", "SG", "CRYPTO"}
    if market.upper() not in valid_markets:
        raise HTTPException(
            status_code=400,
            detail=f"market 参数无效，可选值: HK / US / CN / SG / Crypto",
        )

    # 默认日期范围：过去 30 天 → 今天
    today = datetime.date.today()
    try:
        begin_date = datetime.date.fromisoformat(begin) if begin else today - datetime.timedelta(days=30)
        end_date   = datetime.date.fromisoformat(end)   if end   else today
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误（需 YYYY-MM-DD）: {e}")

    if begin_date > end_date:
        raise HTTPException(status_code=400, detail="begin 不能晚于 end")

    # SDK 限制：范围不超过 1 年
    if (end_date - begin_date).days > 365:
        raise HTTPException(status_code=400, detail="日期范围不能超过 365 天")

    try:
        return await svc.get_trading_days(market, begin_date, end_date)
    except Exception as e:
        logger.exception("get_trading_days failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")
