# main.py
# NIJA Trading Bot — Fully Adaptive, 24/7 Learning

import os
import sys
import importlib
import pkgutil
import platform
import traceback
import logging
from collections import deque
from typing import Optional, Any, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np
from coinbase_advanced_py import Client

# ---------------- Coinbase Client -----------------
c = Client(os.getenv("COINBASE_API_KEY"), os.getenv("COINBASE_API_SECRET"))

# ---------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("coinbase_loader")

# ---------------- Adaptive Trading -----------------
RECENT_TRADES = deque(maxlen=100)  # stores last 100 trades for learning

def update_trade_metrics(order):
    """Update metrics after each trade."""
    try:
        RECENT_TRADES.append({
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "price": float(order.get("price", 0)),
            "quantity": float(order.get("quantity", 0)),
            "tp": float(order.get("take_profit", 0)),
            "sl": float(order.get("stop_loss", 0)),
            "profit": float(order.get("profit", 0)) if "profit" in order else 0
        })
    except Exception:
        pass

def adaptive_risk():
    """Adjust risk dynamically based on recent trades."""
    if not RECENT_TRADES:
        return 0.01
    recent_profits = [t["profit"] for t in RECENT_TRADES if "profit" in t]
    if not recent_profits:
        return 0.01
    avg_profit = sum(recent_profits) / len(recent_profits)
    risk = 0.01 + (avg_profit / 10000)  # scale risk
    return max(0.005, min(risk, 0.05))  # clamp 0.5%-5%

def adaptive_position_size(equity, volatility):
    risk = adaptive_risk()
    size = equity * risk / max(volatility, 0.0001)
    return max(0.001, size)

def adaptive_tp(price, volatility, trend_strength):
    base_tp = price + trend_strength * volatility
    adjustment = np.mean([t["tp"] for t in list(RECENT_TRADES)[-10:] or [0]])
    return base_tp + adjustment * 0.1

def adaptive_sl(price, volatility, trend_strength):
    base_sl = price - trend_strength * volatility
    adjustment = np.mean([t["sl"] for t in list(RECENT_TRADES)[-10:] or [0]])
    return base_sl + adjustment * 0.05

def execute_trade(symbol, side, quantity, price, tp, sl):
    """Place order via Coinbase."""
    order = c.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        type="market",
        take_profit=tp,
        stop_loss=sl
    )
    update_trade_metrics(order)
    return order

# ---------------- FastAPI App -----------------
app = FastAPI(title="NIJA Trading Bot", version="1.0")

# ----- Models -----
class TradeReq(BaseModel):
    symbol: str
    side: str
    price: float
    volatility: float
    trend_strength: float
    equity: float

# ----- Endpoints -----
@app.get("/")
async def root():
    return {"status": "ok", "client_connected": True}

@app.post("/trade")
async def trade(req: TradeReq):
    try:
        quantity = adaptive_position_size(req.equity, req.volatility)
        tp = adaptive_tp(req.price, req.volatility, req.trend_strength)
        sl = adaptive_sl(req.price, req.volatility, req.trend_strength)
        order = execute_trade(req.symbol, req.side, quantity, req.price, tp, sl)
        return {"success": True, "order": order}
    except Exception as e:
        return {"success": False, "error": repr(e), "traceback": traceback.format_exc()}
