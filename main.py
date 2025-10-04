# main.py - NIJA Trading Bot: Adaptive, 24/7, Live Trading
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
from coinbase_advanced_py import Client

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija_trading_bot")

# ---------------- Coinbase Client ----------------
c = Client(os.getenv("COINBASE_API_KEY"), os.getenv("COINBASE_API_SECRET"))

# ---------------- Adaptive Trading Functions ----------------
TRADE_HISTORY = []

def adaptive_position_size(equity, volatility, risk=0.01, trade_history=TRADE_HISTORY):
    factor = 1.0
    if trade_history:
        recent_pnl = sum([t['pnl'] for t in trade_history[-10:]])
        if recent_pnl > 0: factor += 0.2
        elif recent_pnl < 0: factor -= 0.2
    size = equity * risk * factor / max(volatility, 1e-6)
    return max(0.001, size)

def adaptive_tp(price, volatility, trend_strength):
    return price + trend_strength * volatility * 1.1

def adaptive_sl(price, volatility, trend_strength):
    return price - trend_strength * volatility * 1.1

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
        pnl = (tp - price) * quantity if side == "buy" else (price - tp) * quantity
        TRADE_HISTORY.append({"symbol": symbol, "side": side, "pnl": pnl})
        log.info(f"Trade executed: {order}, PnL: {pnl}")
        return order
    except Exception as e:
        log.error(f"Trade failed: {repr(e)}")
        return {"error": repr(e)}

# ---------------- FastAPI ----------------
app = FastAPI(title="NIJA Trading Bot", version="1.0")

class WebhookPayload(BaseModel):
    symbol: str
    side: str
    price: float
    volatility: float
    trend_strength: float
    equity: float

@app.get("/")
async def root():
    return {"status": "NIJA Trading Bot Live", "client_connected": True}

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    try:
        quantity = adaptive_position_size(payload.equity, payload.volatility)
        tp = adaptive_tp(payload.price, payload.volatility, payload.trend_strength)
        sl = adaptive_sl(payload.price, payload.volatility, payload.trend_strength)
        result = execute_trade(payload.symbol, payload.side, quantity, payload.price, tp, sl)
        return {"status": "success", "order": result}
    except Exception as e:
        log.error(f"Webhook processing failed: {repr(e)}")
        raise HTTPException(status_code=500, detail=repr(e))
