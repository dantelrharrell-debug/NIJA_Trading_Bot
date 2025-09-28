# nija_ai.py
import os, json, time, traceback
from decimal import Decimal
import ccxt

# Load API keys from environment
COINBASE_SPOT_KEY = os.getenv("COINBASE_SPOT_KEY")
COINBASE_SPOT_SECRET = os.getenv("COINBASE_SPOT_SECRET")

# Initialize spot client for Coinbase Advanced (use ccxt.coinbase)
spot = None
if COINBASE_SPOT_KEY and COINBASE_SPOT_SECRET:
    try:
        spot = ccxt.coinbase({
            "apiKey": COINBASE_SPOT_KEY,
            "secret": COINBASE_SPOT_SECRET,
            "enableRateLimit": True,
            "timeout": 30000,  # 30s
        })
        print("✅ spot client initialized (coinbase)")
    except Exception as e:
        print("❌ spot init error:", repr(e))
        spot = None
else:
    print("⚠️ spot API keys not found in environment")

TRADE_HISTORY_FILE = "trade_history.json"

def _load_history():
    try:
        with open(TRADE_HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_history(h):
    try:
        with open(TRADE_HISTORY_FILE, "w") as f:
            json.dump(h, f, indent=2)
    except Exception as e:
        print("❌ Failed to save history:", e)

trade_history = _load_history()

def save_entry(symbol, side, amount, entry_price, market_type="spot", note="simulated"):
    entry = {
        "id": f"entry-{int(time.time())}",
        "side": side,
        "amount": float(amount),
        "entry_price": float(entry_price) if entry_price is not None else None,
        "entry_ts": int(time.time()),
        "exit_price": None,
        "exit_ts": None,
        "profit_percent": None,
        "market_type": market_type,
        "note": note
    }
    trade_history.setdefault(symbol, []).append(entry)
    _save_history(trade_history)
    return entry

def last_trade_profit_percent(symbol):
    entries = trade_history.get(symbol, [])
    for e in reversed(entries):
        if e.get("profit_percent") is not None:
            return float(e["profit_percent"])
    return None

def ai_adjust_amount(symbol, base_amount):
    try:
        entries = trade_history.get(symbol, [])
        wins = sum(1 for t in entries if (t.get("profit_percent") or 0) > 0)
        losses = sum(1 for t in entries if (t.get("profit_percent") or 0) < 0)
        multiplier = 1 + (wins - losses) * 0.08
        multiplier = max(0.1, min(multiplier, 3.0))
        return float(Decimal(str(base_amount)) * Decimal(str(multiplier)))
    except Exception as e:
        print("ai_adjust_amount failed:", e)
        traceback.print_exc()
        return float(base_amount)

def _get_price_from_order(order):
    try:
        return order.get("average") or order.get("price") or None
    except Exception:
        return None

def execute_trade(symbol, side, amount, market_type="spot", dry_run=True):
    """
    amount: in base coin units (e.g., BTC quantity). If you pass USD notional,
            call convert_usd_to_qty() first.
    dry_run: True -> simulate, False -> live
    """
    client = spot
    if dry_run or not client:
        # simulate using last ticker if we can
        last_price = None
        try:
            t = client.fetch_ticker(symbol) if client else None
            last_price = (t.get("last") or t.get("close")) if t else None
        except Exception:
            last_price = None
        entry = save_entry(symbol, side, amount, last_price, market_type=market_type, note="simulated")
        print("🟡 Simulated trade recorded:", entry)
        return {"simulated": True, "entry": entry}

    try:
        # Use create_order for broad compatibility
        order = client.create_order(symbol, "market", side, float(amount))
        exec_price = _get_price_from_order(order)
        if not exec_price:
            try:
                t = client.fetch_ticker(symbol)
                exec_price = (t.get("last") or t.get("close")) if t else None
            except Exception:
                exec_price = None
        entry = save_entry(symbol, side, amount, exec_price, market_type=market_type, note="live")
        print("✅ Live trade executed and recorded:", entry)
        return {"order": order, "entry": entry}
    except Exception as e:
        print("❌ execute_trade failed:", repr(e))
        traceback.print_exc()
        return {"error": str(e)}

def convert_usd_to_qty(symbol, usd_amount):
    """
    Convert USD notional to base coin quantity using last price.
    Example: convert_usd_to_qty("BTC-USD", 10) -> ~0.00025 BTC
    Returns Decimal or None on error.
    """
    if not spot:
        print("⚠️ spot client not configured for price lookup")
        return None
    try:
        t = spot.fetch_ticker(symbol)
        last = t.get("last") or t.get("close")
        if last:
            last_d = Decimal(str(last))
            qty = Decimal(str(usd_amount)) / last_d
            return float(qty)
    except Exception as e:
        print("❌ convert_usd_to_qty error:", repr(e))
    return None
