# --- BEGIN robust-import-and-debug for coinbase client ---
import sys
import site
import os
import importlib
import traceback

print("=== DEBUG START ===")
print("sys.executable:", sys.executable)
print("python version:", sys.version)
print("First 20 sys.path entries:")
for p in sys.path[:20]:
    print("  ", p)

# show typical site-packages locations
try:
    sp = site.getsitepackages()
    print("site.getsitepackages():")
    for p in sp:
        print("  ", p)
except Exception as e:
    print("site.getsitepackages() failed:", e)

# show user site-packages
try:
    up = site.getusersitepackages()
    print("site.getusersitepackages():", up)
except Exception as e:
    print("site.getusersitepackages() failed:", e)

# list coinbase-related files in paths we can access
candidates_found = []
paths_to_search = sys.path[:]  # search entire sys.path (limited to first 40 entries below)
for p in paths_to_search[:40]:
    try:
        if not p or not os.path.exists(p):
            continue
        for fname in os.listdir(p):
            name = fname.lower()
            if name.startswith("coinbase") or "coinbase" in name:
                candidates_found.append(os.path.join(p, fname))
    except Exception:
        pass

print("Coinbase-related files/dirs found (first 30):")
for i, f in enumerate(candidates_found[:30]):
    print(f"  {i+1}. {f}")

# Try a series of likely import names and stop on the first that works
import_names = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_advanced_py.client",
    "coinbase.advanced",   # unlikely but harmless to try
    "coinbase"             # just in case package nested
]

cb = None
successful_name = None
for name in import_names:
    try:
        mod = importlib.import_module(name)
        cb = mod
        successful_name = name
        print(f"✅ Successfully imported '{name}' as cb")
        break
    except Exception as e:
        print(f"Import failed for '{name}': {e.__class__.__name__}: {e}")

if cb is None:
    print("❌ Could not import any of the expected module names. Full traceback for the last attempt:")
    traceback.print_exc()
    print()
    print("If the build logs showed 'Successfully installed coinbase-advanced-py-1.8.2', but imports still fail:")
    print("- Confirm your requirements.txt contains exactly: coinbase-advanced-py==1.8.2")
    print("- Ensure Render rebuilt after that change (trigger a redeploy).")
    print("- If installed in a path not shown in sys.path, we can add it with site.addsitedir(path).")
    print("- Paste the above DEBUG output to me and I will tell you the exact site.addsitedir(...) line to add.")
else:
    # expose 'cb' to rest of module
    globals()["cb"] = cb
    globals()["_COINBASE_IMPORT_NAME"] = successful_name

print("=== DEBUG END ===\n")
# --- END robust-import-and-debug for coinbase client ---
# main.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Try the correct import for the installed package
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    # Helpful message in logs — if you see this, fix requirements.txt and redeploy
    raise ModuleNotFoundError("Module 'coinbase_advanced_py' not found. Ensure requirements.txt contains 'coinbase-advanced-py==1.8.2' and redeploy.")

# Load env
load_dotenv()

# ----------------------------
# Configuration (env or fallback)
# ----------------------------
API_KEY = os.getenv("API_KEY") or "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = os.getenv("API_SECRET") or "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or "MySuperStrongSecret123!"  # change in env for security

MIN_RISK_PERCENT = float(os.getenv("MIN_RISK_PERCENT", 2.0))   # 2%
MAX_RISK_PERCENT = float(os.getenv("MAX_RISK_PERCENT", 10.0))  # 10%
MIN_TRADE_AMOUNT_USD = float(os.getenv("MIN_TRADE_AMOUNT", 10.0))  # minimum USD per trade

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ----------------------------
# Coinbase client
# ----------------------------
client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)
logging.info("CoinbaseAdvanced client initialized")

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="Nija Trading Bot - Webhook Receiver")

class WebhookPayload(BaseModel):
    secret: str
    symbol: str            # e.g., "BTC-USD"
    side: str              # "buy" or "sell"
    risk_percent: float = None  # optional, percent (e.g., 5.0 for 5%). If not provided, AI/default used.
    # Accept additional fields TradingView may send:
    price: float | None = None
    comment: str | None = None

# ----------------------------
# Helpers
# ----------------------------
def get_usd_balance() -> float:
    """Return current USD available balance as float."""
    accounts = client.get_accounts()
    for a in accounts:
        if a.get("currency") == "USD":
            return float(a.get("balance", 0.0))
    return 0.0

def clamp_risk(risk_percent: float) -> float:
    """Ensure risk_percent is between MIN and MAX."""
    return max(MIN_RISK_PERCENT, min(MAX_RISK_PERCENT, float(risk_percent)))

def calculate_trade_amount_usd(balance_usd: float, risk_percent: float) -> float:
    """Return USD sized trade (rounded to 2 decimals), respecting MIN_TRADE_AMOUNT_USD."""
    usd = round(balance_usd * (risk_percent / 100.0), 2)
    if usd < MIN_TRADE_AMOUNT_USD:
        return MIN_TRADE_AMOUNT_USD
    return usd

def place_market_order(product_id: str, side: str, funds_usd: float):
    """
    Use Coinbase Advanced place_order with 'funds' to specify USD amount for market orders.
    Returns the order dict/object from the client or raises Exception.
    """
    return client.place_order(product_id=product_id, side=side, order_type="market", funds=str(funds_usd))

# ----------------------------
# Webhook endpoint
# ----------------------------
@app.post("/webhook", response_model=dict)
async def webhook(payload: WebhookPayload, request: Request):
    # 1) Validate secret
    if payload.secret != WEBHOOK_SECRET:
        logging.warning("Webhook: unauthorized access attempt.")
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 2) Validate side
    side = payload.side.lower()
    if side not in ("buy", "sell"):
        logging.warning("Webhook: invalid side: %s", payload.side)
        raise HTTPException(status_code=400, detail="Invalid side (must be 'buy' or 'sell')")

    symbol = payload.symbol.upper()
    logging.info("Webhook received: %s %s (raw risk=%s)", side, symbol, payload.risk_percent)

    # 3) Determine risk (clamped to 2%-10%). If risk not provided, use default mid-point 5%
    requested_risk = payload.risk_percent if payload.risk_percent is not None else (MIN_RISK_PERCENT + MAX_RISK_PERCENT) / 2.0
    risk = clamp_risk(requested_risk)

    # 4) Check USD balance
    usd_balance = get_usd_balance()
    if usd_balance <= 0:
        logging.error("Webhook: no USD balance available.")
        raise HTTPException(status_code=400, detail="No USD balance available")

    # 5) Calculate trade size in USD
    trade_usd = calculate_trade_amount_usd(usd_balance, risk)
    logging.info("Webhook: usd_balance=%.2f risk=%.2f%% trade_usd=%.2f", usd_balance, risk, trade_usd)

    # 6) Place market order
    try:
        order = place_market_order(product_id=symbol, side=side, funds_usd=trade_usd)
        logging.info("Order successful: %s", order)
        return {
            "status": "success",
            "symbol": symbol,
            "side": side,
            "risk_percent": risk,
            "trade_usd": trade_usd,
            "order": order
        }
    except Exception as e:
        logging.exception("Order placement failed:")
        raise HTTPException(status_code=500, detail=f"Order placement failed: {e}")

@app.get("/health")
async def health():
    return {"status": "ok"}

# ----------------------------
# Run with: uvicorn main:app --host 0.0.0.0 --port 8000
# (Render start command: uvicorn main:app --host 0.0.0.0 --port $PORT)
# ----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
