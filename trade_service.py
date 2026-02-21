import logging
from decimal import Decimal

from longport.openapi import Config, AsyncTradeContext

logger = logging.getLogger(__name__)


def _d(v) -> str:
    """Decimal / float / None → 字符串，保留精度。"""
    if v is None:
        return "0"
    return str(v)


class TradeService:
    """封装 LongPort AsyncTradeContext，提供资产查询能力。"""

    def __init__(self):
        self._ctx: AsyncTradeContext | None = None

    async def start(self):
        config = Config.from_env()
        self._ctx = await AsyncTradeContext.create(config)
        logger.info("LongPort TradeContext initialized.")

    # ------------------------------------------------------------------ #
    # 账户余额
    # ------------------------------------------------------------------ #

    async def get_account_balance(self, currency: str | None = None) -> list[dict]:
        """
        返回各子账户余额。
        currency: 指定货币筛选（如 'USD'/'HKD'），None 表示全部。
        """
        items = await self._ctx.account_balance(currency=currency)
        result = []
        for item in items:
            cash_infos = []
            for ci in (getattr(item, "cash_infos", []) or []):
                cash_infos.append({
                    "currency":      str(getattr(ci, "currency", "")),
                    "available_cash": _d(getattr(ci, "available_cash", None)),
                    "withdraw_cash":  _d(getattr(ci, "withdraw_cash", None)),
                    "frozen_cash":    _d(getattr(ci, "frozen_cash", None)),
                    "settling_cash":  _d(getattr(ci, "settling_cash", None)),
                })
            result.append({
                "currency":               str(getattr(item, "currency", "")),
                "net_assets":             _d(getattr(item, "net_assets", None)),
                "total_cash":             _d(getattr(item, "total_cash", None)),
                "buy_power":              _d(getattr(item, "buy_power", None)),
                "init_margin":            _d(getattr(item, "init_margin", None)),
                "maintenance_margin":     _d(getattr(item, "maintenance_margin", None)),
                "margin_call":            _d(getattr(item, "margin_call", None)),
                "risk_level":             int(getattr(item, "risk_level", 0) or 0),
                "max_finance_amount":     _d(getattr(item, "max_finance_amount", None)),
                "remaining_finance_amount": _d(getattr(item, "remaining_finance_amount", None)),
                "cash_infos":             cash_infos,
            })
        return result

    # ------------------------------------------------------------------ #
    # 股票持仓
    # ------------------------------------------------------------------ #

    async def get_stock_positions(self, symbols: list[str] | None = None) -> list[dict]:
        """
        返回所有子账户的股票持仓。
        symbols: 按标的过滤，None 表示全部。
        """
        resp = await self._ctx.stock_positions(symbols=symbols or None)
        result = []
        for ch in (getattr(resp, "channels", []) or []):
            account_channel = str(getattr(ch, "account_channel", ""))
            for pos in (getattr(ch, "positions", []) or []):
                init_qty = getattr(pos, "init_quantity", None)
                result.append({
                    "account_channel":    account_channel,
                    "symbol":             str(getattr(pos, "symbol", "")),
                    "symbol_name":        str(getattr(pos, "symbol_name", "")),
                    "market":             str(getattr(pos, "market", "")).split(".")[-1],
                    "currency":           str(getattr(pos, "currency", "")),
                    "quantity":           int(getattr(pos, "quantity", 0) or 0),
                    "available_quantity": int(getattr(pos, "available_quantity", 0) or 0),
                    "init_quantity":      int(init_qty) if init_qty is not None else None,
                    "cost_price":         _d(getattr(pos, "cost_price", None)),
                })
        return result

    # ------------------------------------------------------------------ #
    # 基金持仓
    # ------------------------------------------------------------------ #

    async def get_fund_positions(self, symbols: list[str] | None = None) -> list[dict]:
        """返回基金持仓（若未持有基金则返回空数组）。"""
        resp = await self._ctx.fund_positions(symbols=symbols or None)
        result = []
        for ch in (getattr(resp, "channels", []) or []):
            account_channel = str(getattr(ch, "account_channel", ""))
            for pos in (getattr(ch, "positions", []) or []):
                result.append({
                    "account_channel":       account_channel,
                    "symbol":                str(getattr(pos, "symbol", "")),
                    "symbol_name":           str(getattr(pos, "symbol_name", "")),
                    "currency":              str(getattr(pos, "currency", "")),
                    "holding_units":         _d(getattr(pos, "holding_units", None)),
                    "current_net_asset_value": _d(getattr(pos, "current_net_asset_value", None)),
                    "cost_net_asset_value":  _d(getattr(pos, "cost_net_asset_value", None)),
                    "net_asset_value_day":   str(getattr(pos, "net_asset_value_day", "") or ""),
                })
        return result
