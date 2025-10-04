import os

print("\n=== NIJA TRADING BOT DEBUG & AUTO-ENABLE ===\n")

# Check Python version
import sys
print(f"Python version: {sys.version}")

# Check if API keys are set
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
print(f"API_KEY present: {bool(api_key)}")
print(f"API_SECRET present: {bool(api_secret)}")

# Initialize trading flag
TRADING_ENABLED = False

# Try importing Coinbase Advanced
try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py detected!")
except ImportError:
    print("❌ coinbase_advanced_py NOT detected!")

# Try initializing Coinbase client
client = None
if api_key and api_secret:
    try:
        client = coinbase_advanced_py.Client(api_key, api_secret)
        print("✅ Coinbase client initialized successfully!")
        TRADING_ENABLED = True
    except Exception as e:
        print("❌ Coinbase client failed to initialize!")
        print("Error:", e)
else:
    print("⚠️ Cannot initialize Coinbase client — missing API keys")

# Final status
if TRADING_ENABLED:
    print("🔥 Trading ENABLED!")
else:
    print("⚠️ Trading DISABLED!")

print("\n=== NIJA TRADING BOT DEBUG & AUTO-ENABLE END ===\n")
try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py detected!")
except ImportError:
    print("❌ coinbase_advanced_py NOT detected!")
# main.py — NIJA Trading Bot single-file app (drop-in)
import os
import sys
import logging
import traceback
import importlib
import pkgutil
from typing import Optional, Any, Dict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# load .env locally if present (safe — in prod you should use platform env vars)
load_dotenv()

# logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija")

# Try optional imports
NUMPY_AVAILABLE = True
try:
    import numpy as np
except Exception:
    NUMPY_AVAILABLE = False
    log.warning("numpy not available; adaptive math will fall back to simple math.")

COINBASE_MODULE_NAME = "coinbase_advanced_py"
COINBASE_AVAILABLE = True
try:
    coinbase_mod = importlib.import_module(COINBASE_MODULE_NAME)
    # try to find a reasonable client class
    Client = getattr(coinbase_mod, "Client", None) or getattr(coinbase_mod, "WalletClient", None) or getattr(coinbase_mod, "CoinbaseClient", None)
    if not Client:
        # keep module reference but mark client not found
        COINBASE_AVAILABLE = False
        log.warning("Module %s found but no Client class discovered.", COINBASE_MODULE_NAME)
except ModuleNotFoundError:
    coinbase_mod = None
    Client = None
    COINBASE_AVAILABLE = False
    log.warning("%s not installed.", COINBASE_MODULE_NAME)
except Exception:
    coinbase_mod = None
    Client = None
    COINBASE_AVAILABLE = False
    log.warning("Error importing %s: %s", COINBASE_MODULE_NAME, traceback.format_exc())

# environment variables expected
ENV_API_KEY = os.getenv("API_KEY") or os.getenv("COINBASE_API_KEY") or os.getenv("COINBASE_API_KEY")
ENV_API_SECRET = os.getenv("API_SECRET") or os.getenv("COINBASE_API_SECRET") or os.getenv("COINBASE_API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # optional for webhook auth

TRADING_ENABLED = COINBASE_AVAILABLE and Client is not None and bool(ENV_API_KEY) and bool(ENV_API_SECRET)

if TRADING_ENABLED:
    try:
        cb_client = Client(ENV_API_KEY, ENV_API_SECRET)
        log.info("Coinbase client instantiated successfully.")
    except Exception as e:
        cb_client = None
        TRADING_ENABLED = False
        log.warning("Failed to instantiate Coinbase client: %s", repr(e))
else:
    cb_client = None
    log.warning("Trading DISABLED. coinbase client present: %s, client class: %s, api keys present: %s",
                COINBASE_AVAILABLE, bool(Client), bool(ENV_API_KEY and ENV_API_SECRET))

# ---------- adaptive helpers ----------
def safe_float(x, fallback=0.0):
    try:
        return float(x)
    except Exception:
        return fallback

def adaptive_position_size(equity: float, volatility: float, risk: float = 0.01) -> float:
    """
    Very simple risk-based sizing:
      - risk = fraction of equity to risk per trade (default 1%)
      - volatility = some measure (e.g. ATR). Must be provided by your strategy
    Returns: position size (in base units). Adjust for your product conventions.
    """
    equity = safe_float(equity, 0.0)
    volatility = max(1e-8, safe_float(volatility, 1.0))
    size = (equity * risk) / volatility
    if NUMPY_AVAILABLE:
        return float(max(0.001, size))
    else:
        return max(0.001, size)

def adaptive_tp(price: float, volatility: float, trend_strength: float = 1.0) -> float:
    price = safe_float(price)
    volatility = safe_float(volatility, 0.0)
    trend_strength = safe_float(trend_strength, 1.0)
    return price + (trend_strength * volatility)

def adaptive_sl(price: float, volatility: float, trend_strength: float = 1.0) -> float:
    price = safe_float(price)
    volatility = safe_float(volatility, 0.0)
    trend_strength = safe_float(trend_strength, 1.0)
    return price - (trend_strength * volatility)

# ---------- FastAPI app ----------
app = FastAPI(title="NIJA Trading Bot", version="1.0")

@app.get("/")
def root():
    return {
        "status": "Bot is live",
        "coinbase_client_detected": COINBASE_AVAILABLE and Client is not None,
        "api_keys_present": bool(ENV_API_KEY and ENV_API_SECRET),
        "trading_enabled": TRADING_ENABLED
    }

@app.get("/diag")
def diag():
    # Lightweight diagnostic
    installed = []
    try:
        for _, name, _ in pkgutil.iter_modules():
            installed.append(name)
            if len(installed) >= 300:
                break
    except Exception:
        installed = ["error_listing"]
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "client_module_attempt": COINBASE_MODULE_NAME,
        "coinbase_module_loaded": COINBASE_AVAILABLE,
        "client_class_found": bool(Client),
        "api_keys_env": bool(ENV_API_KEY and ENV_API_SECRET),
        "trading_enabled": TRADING_ENABLED,
        "installed_sample_count": len(installed),
        "installed_sample": installed[:120],
    }

@app.get("/modules")
def modules():
    # returns a small sample of sys.modules for debugging in the deployed instance
    keys = sorted(list(sys.modules.keys()))
    return {"modules_sample": keys[:200]}

# allow instantiation attempt via POST for remote testing
class InstReq(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

@app.post("/instantiate")
def instantiate(req: InstReq):
    if not COINBASE_AVAILABLE or Client is None:
        raise HTTPException(status_code=400, detail=f"No Coinbase client available ({COINBASE_MODULE_NAME})")
    ak = req.api_key or ENV_API_KEY
    sk = req.api_secret or ENV_API_SECRET
    if not ak or not sk:
        raise HTTPException(status_code=400, detail="No API key/secret provided")
    try:
        inst = Client(ak, sk)
        return {"ok": True, "repr": repr(inst)[:500]}
    except Exception as e:
        return {"ok": False, "error": repr(e)}

# ---------- trade endpoint (guarded) ----------
class TradeReq(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: Optional[float] = None
    price: Optional[float] = None
    equity: Optional[float] = None
    volatility: Optional[float] = None
    trend_strength: Optional[float] = 1.0
    test: Optional[bool] = True  # default test (no real order)

@app.post("/trade")
def trade(req: TradeReq):
    if not TRADING_ENABLED or cb_client is None:
        raise HTTPException(status_code=400, detail="Trading disabled: client or API keys missing.")
    # compute quantity if missing and equity/volatility provided
    qty = req.quantity
    if qty is None:
        if req.equity is None or req.volatility is None:
            raise HTTPException(status_code=400, detail="quantity missing — provide quantity or (equity+volatility)")
        qty = adaptive_position_size(req.equity, req.volatility)
    price = req.price or None
    tp = adaptive_tp(price if price else 0.0, req.volatility or 0.0, req.trend_strength or 1.0)
    sl = adaptive_sl(price if price else 0.0, req.volatility or 0.0, req.trend_strength or 1.0)
    payload = {
        "symbol": req.symbol,
        "side": req.side,
        "quantity": float(qty),
        "price": price,
        "take_profit": tp,
        "stop_loss": sl,
        "type": "market"
    }
    # Attempt to place an order using common client methods but guard everything
    info = {"payload": payload, "called": None, "result": None, "error": None}
    try:
        client = cb_client
        # common method variations
        if hasattr(client, "place_order"):
            info["called"] = "place_order"
            if req.test:
                info["result"] = "TEST_MODE: order not sent. payload_preview=" + repr(payload)
            else:
                res = client.place_order(**{k: v for k, v in payload.items() if v is not None})
                info["result"] = repr(res)[:2000]
        elif hasattr(client, "create_order"):
            info["called"] = "create_order"
            if req.test:
                info["result"] = "TEST_MODE: create_order not executed. payload_preview=" + repr(payload)
            else:
                # try keyword then positional
                try:
                    res = client.create_order(**payload)
                except TypeError:
                    res = client.create_order(req.symbol, req.side, qty, price)
                info["result"] = repr(res)[:2000]
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            info["called"] = "client.orders.create"
            if req.test:
                info["result"] = "TEST_MODE: client.orders.create not executed. payload_preview=" + repr(payload)
            else:
                res = client.orders.create(payload)
                info["result"] = repr(res)[:2000]
        else:
            info["error"] = "No known order API on client. Inspect client object."
    except Exception as e:
        info["error"] = repr(e)
    return info

# ---------- webhook listener (TradingView friendly) ----------
@app.post("/webhook")
async def webhook(request: Request):
    """
    Expect JSON payload from TradingView (customize your message template on TradingView).
    Example TradingView message (json):
    {
      "secret":"<WEBHOOK_SECRET>",
      "symbol":"BTC-USD",
      "action":"buy",
      "price":42000,
      "volatility": 120,
      "equity": 1000
    }
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    # optional auth
    if WEBHOOK_SECRET:
        if data.get("secret") != WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized webhook secret")
    # required fields
    symbol = data.get("symbol")
    action = data.get("action")  # "buy" or "sell"
    if not symbol or not action:
        raise HTTPException(status_code=400, detail="Missing symbol or action")
    # build a trade request using payload fields if present
    trade_payload = TradeReq(
        symbol=symbol,
        side=action,
        quantity=data.get("quantity"),
        price=data.get("price"),
        equity=data.get("equity"),
        volatility=data.get("volatility"),
        trend_strength=data.get("trend_strength", 1.0),
        test=bool(data.get("test", True))
    )
    # If trading disabled: return diagnostic only
    if not TRADING_ENABLED:
        log.warning("Webhook received but trading disabled. Payload: %s", data)
        return {"status": "trading_disabled", "payload": data}
    # Otherwise call our trade function
    resp = trade(trade_payload)
    log.info("Executed trade via webhook: %s -> resp keys: %s", symbol, list(resp.keys()))
    return {"status": "ok", "trade_response": resp}

# run instructions are left to the host (uvicorn, render)
