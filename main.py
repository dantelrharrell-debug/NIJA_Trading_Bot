# main.py
# NIJA Trading Bot - Coinbase Advanced Py + Adaptive Trading
# Single-file FastAPI entrypoint with live webhook for TradingView alerts

import os
import sys
import pkgutil
import platform
import importlib
import importlib.util
import logging
import traceback
from typing import Optional, Any, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import numpy as np
from coinbase_advanced_py import Client

# ------------------ Coinbase Client ------------------
c = Client(os.getenv("COINBASE_API_KEY"), os.getenv("COINBASE_API_SECRET"))

def adaptive_position_size(equity, volatility, risk=0.01):
    size = equity * risk / max(volatility, 0.0001)
    return max(0.001, size)

def adaptive_tp(price, volatility, trend_strength):
    return price + trend_strength * volatility

def adaptive_sl(price, volatility, trend_strength):
    return price - trend_strength * volatility

def execute_trade(symbol, side, quantity, price, tp, sl):
    try:
        order = c.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            type="market",
            take_profit=tp,
            stop_loss=sl
        )
        return order
    except Exception as e:
        return {"error": repr(e)}

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija_trading_bot")

# ------------------ FastAPI App ------------------
app = FastAPI(title="NIJA Trading Bot", version="1.0")

# ------------------ Webhook Endpoint for TradingView ------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        symbol = data["symbol"]
        side = data["side"]
        price = float(data["price"])
        equity = float(data.get("account_equity", 1000))
        volatility = float(data.get("volatility", 1))
        trend_strength = float(data.get("trend_strength", 1))

        quantity = adaptive_position_size(equity, volatility)
        tp = adaptive_tp(price, volatility, trend_strength)
        sl = adaptive_sl(price, volatility, trend_strength)

        order = execute_trade(symbol, side, quantity, price, tp, sl)
        return {"status": "success", "order": repr(order)}
    except Exception as e:
        return {"status": "error", "message": repr(e), "traceback": traceback.format_exc()}

# ------------------ Diagnostic Endpoints ------------------
@app.get("/")
async def root():
    return {"status": "ok", "client_connected": True}

@app.get("/diag")
async def diag():
    try:
        site_paths = []
        import site
        site_paths = site.getsitepackages() if hasattr(site, "getsitepackages") else [site.getusersitepackages()]
    except Exception:
        site_paths = [p for p in sys.path if "site-packages" in p or "dist-packages" in p][:6]

    response = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "sys_path_sample": sys.path[:80],
        "site_paths": site_paths,
    }
    return JSONResponse(content=response)

# ------------------ Optional Trade Test Endpoint ------------------
class TradeReq(BaseModel):
    symbol: str
    side: str
    price: float
    size: Optional[float] = None
    test: Optional[bool] = True

@app.post("/trade")
async def trade(req: TradeReq):
    quantity = req.size or 0.001
    tp = req.price + 1  # simple demo
    sl = req.price - 1  # simple demo
    order = execute_trade(req.symbol, req.side, quantity, req.price, tp, sl)
    return {"status": "success", "order": repr(order)}
