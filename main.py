"""
JiangEquityRequestAPI Python 后端入口
运行: python main.py  (或由 Swift PythonBridge 启动)

启动前请在 config.py 中填写 LongPort API 凭证。
"""
import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ---- 优先从 config.py 注入环境变量（硬编码凭证），再初始化 SDK ----
import config

os.environ.setdefault("LONGPORT_APP_KEY",      config.LONGPORT_APP_KEY)
os.environ.setdefault("LONGPORT_APP_SECRET",   config.LONGPORT_APP_SECRET)
os.environ.setdefault("LONGPORT_ACCESS_TOKEN", config.LONGPORT_ACCESS_TOKEN)

from quote_service import QuoteService
from trade_service import TradeService
from websocket_manager import WebSocketManager
from routers import quotes as quotes_router
from routers import watchlist as watchlist_router
from routers import fundamental as fundamental_router
from routers import assets as assets_router
from routers import market as market_router

# --------------------------------------------------------------------------- #
# 日志
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Lifespan（替代 on_event，兼容 FastAPI 0.93+）
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    ws_manager = WebSocketManager()

    async def push_callback(msg_type: str, symbol: str, data: dict):
        await ws_manager.broadcast({"type": msg_type, "symbol": symbol, "data": data})

    svc = QuoteService(push_callback)
    await svc.start()

    trade_svc = TradeService()
    await trade_svc.start()

    app.state.quote_service = svc
    app.state.trade_service = trade_svc
    app.state.ws_manager = ws_manager
    logger.info("JiangEquityRequestAPI backend started.")

    yield  # 应用运行阶段

    # --- shutdown ---
    logger.info("JiangEquityRequestAPI backend shutting down.")


# --------------------------------------------------------------------------- #
# FastAPI App
# --------------------------------------------------------------------------- #
app = FastAPI(title="JiangEquityRequestAPI Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes_router.router)
app.include_router(watchlist_router.router)
app.include_router(fundamental_router.router)
app.include_router(assets_router.router)
app.include_router(market_router.router)

# --------------------------------------------------------------------------- #
# 基础路由
# --------------------------------------------------------------------------- #
@app.get("/health")
async def health():
    svc = app.state.quote_service
    resp = {
        "status": "ok",
        "subscribed": svc.subscribed_symbols,
        "ws_clients": app.state.ws_manager.client_count,
    }
    if config.PUBLIC_BASE_URL:
        resp["public_base_url"] = config.PUBLIC_BASE_URL
    return resp


# --------------------------------------------------------------------------- #
# WebSocket 实时行情通道
# --------------------------------------------------------------------------- #
@app.websocket("/ws/quotes")
async def ws_quotes(websocket: WebSocket):
    manager: WebSocketManager = app.state.ws_manager
    svc: QuoteService = app.state.quote_service

    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                action = msg.get("action", "")
                symbols = msg.get("symbols", [])

                if action == "subscribe" and symbols:
                    await svc.subscribe(symbols)
                    await websocket.send_text(json.dumps({
                        "type": "ack",
                        "action": "subscribe",
                        "symbols": symbols,
                        "subscribed": svc.subscribed_symbols,
                    }))

                elif action == "unsubscribe" and symbols:
                    await svc.unsubscribe(symbols)
                    await websocket.send_text(json.dumps({
                        "type": "ack",
                        "action": "unsubscribe",
                        "symbols": symbols,
                        "subscribed": svc.subscribed_symbols,
                    }))

                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"未知 action: {action}",
                    }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "JSON 解析失败"}))

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    port = int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[1] == "--port" else config.SERVER_PORT
    logger.info(f"Starting uvicorn on {config.SERVER_HOST}:{port}")
    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=port,
        log_level="info",
    )
