"""
资产相关 REST 路由。

端点：
  GET /api/assets/balance              账户余额（净资产、现金、保证金等）
  GET /api/assets/balance?currency=USD 指定货币筛选
  GET /api/assets/positions            股票持仓
  GET /api/assets/positions?symbols=AAPL.US,700.HK  按标的筛选
  GET /api/assets/fund_positions       基金持仓
"""
import logging

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/assets", tags=["assets"])
logger = logging.getLogger(__name__)


def _svc(request: Request):
    return request.app.state.trade_service


@router.get("/balance")
async def get_account_balance(request: Request, currency: str | None = None):
    """
    查询账户余额。

    - `net_assets`: 净资产
    - `total_cash`: 现金总额（含负值代表融资）
    - `buy_power`: 购买力
    - `init_margin` / `maintenance_margin`: 初始/维持保证金
    - `cash_infos`: 各货币现金明细

    示例: GET /api/assets/balance
    示例: GET /api/assets/balance?currency=USD
    """
    try:
        return await _svc(request).get_account_balance(currency=currency)
    except Exception as e:
        logger.exception("get_account_balance failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/positions")
async def get_stock_positions(request: Request, symbols: str | None = None):
    """
    查询股票持仓。

    - `symbols`: 可选，逗号分隔的标的过滤，如 `AAPL.US,700.HK`

    示例: GET /api/assets/positions
    示例: GET /api/assets/positions?symbols=AAPL.US,700.HK
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else None
    try:
        return await _svc(request).get_stock_positions(symbol_list)
    except Exception as e:
        logger.exception("get_stock_positions failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")


@router.get("/fund_positions")
async def get_fund_positions(request: Request, symbols: str | None = None):
    """
    查询基金持仓（未持有基金时返回空数组）。

    示例: GET /api/assets/fund_positions
    """
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else None
    try:
        return await _svc(request).get_fund_positions(symbol_list)
    except Exception as e:
        logger.exception("get_fund_positions failed: %s", e)
        raise HTTPException(status_code=500, detail="internal server error")
