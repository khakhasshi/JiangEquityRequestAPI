from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class QuoteSnapshot(BaseModel):
    symbol: str
    name: str
    last_done: str
    open: str
    high: str
    low: str
    prev_close: str
    volume: int
    turnover: str
    change: str
    change_pct: str
    timestamp: int
    is_up: bool


class CandlestickItem(BaseModel):
    timestamp: int
    open: str
    close: str
    high: str
    low: str
    volume: int
    turnover: str


class DepthLevel(BaseModel):
    price: str
    volume: int
    order_num: int


class MarketDepth(BaseModel):
    symbol: str
    asks: list[DepthLevel]
    bids: list[DepthLevel]


class SubscribeRequest(BaseModel):
    symbols: list[str]


class WatchlistAddRequest(BaseModel):
    symbol: str


class PushMessage(BaseModel):
    type: str          # "quote" | "candlestick"
    symbol: str
    data: dict
