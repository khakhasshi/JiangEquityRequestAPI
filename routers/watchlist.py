"""
自选股持久化路由（JSON 文件存储，无需数据库）。
"""
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from models import WatchlistAddRequest

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

# 自选股数据存储在用户主目录下
_WATCHLIST_FILE = Path.home() / ".jiang_equity_request_watchlist.json"


def _load() -> list[str]:
    if _WATCHLIST_FILE.exists():
        try:
            return json.loads(_WATCHLIST_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(symbols: list[str]):
    _WATCHLIST_FILE.write_text(
        json.dumps(symbols, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@router.get("")
async def get_watchlist():
    """获取自选股列表。"""
    return {"symbols": _load()}


@router.post("")
async def add_to_watchlist(body: WatchlistAddRequest):
    """添加股票到自选股。"""
    symbols = _load()
    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol 不能为空")
    if symbol not in symbols:
        symbols.append(symbol)
        _save(symbols)
    return {"symbols": symbols}


@router.delete("/{symbol:path}")
async def remove_from_watchlist(symbol: str):
    """从自选股删除股票。"""
    symbols = _load()
    symbol = symbol.strip().upper()
    if symbol not in symbols:
        raise HTTPException(status_code=404, detail=f"{symbol} 不在自选股中")
    symbols.remove(symbol)
    _save(symbols)
    return {"symbols": symbols}
