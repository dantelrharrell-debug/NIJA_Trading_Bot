try:
    from coinbase_advanced_py import Client
    print("Coinbase client module loaded ✅")
except ModuleNotFoundError:
    print("❌ Coinbase client module NOT FOUND")
# main.py (Live Autonomous NIJA Trading Bot)
import os
import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from coinbase_advanced_py import Client
import uvicorn

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("nija_trading_bot")

# ---------- Load Env ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", 8000))

if not API_KEY or not API_SECRET:
    log.error("API_KEY or API_SECRET missing!")
    raise EnvironmentError("API_KEY and API_SECRET must be set in .env")

# ---------- Coinbase Client ----------
try:
    client = Client(API_KEY, API_SECRET)
    log.info("Coinbase client initialized ✅")
except Exception as e:
    log.error("Failed to initialize Coinbase client: %s", e)
    raise e

# ---------- FastAPI ----------
app = FastAPI(title="NIJA Trading Bot Live")

# ---------- Pydantic Model ----------
class TradeSignal(BaseModel):
    symbol: str      # e.g., BTC, ETH
    action: str      # buy or sell
    size: float      # USD amount or crypto units

# ---------- Helper Functions ----------
def safe_execute_trade(symbol: str, action: str, size: float):
    """Executes trade safely, logs before sending."""
    if size <= 0:
        log.warning("Trade size invalid, skipping: %s %s %s", action, size, symbol)
        return {"status": "skipped", "reason": "invalid size"}

    product_id = f"{symbol}-USD"
    log.info("Placing %s order: %s %s", action, size, product_id)

    try:
        if action.lower() == "buy":
            order = client.place_market_order(product_id=product_id, side="buy", funds=str(size))
        elif action.lower() == "sell":
            order = client.place_market_order(product_id=product_id, side="sell", size=str(size))
        else:
            log.warning("Unknown action received: %s", action)
            return {"status": "error", "detail": "Unknown action"}
        
        log.info("Trade executed successfully: %s", order)
        return {"status": "success", "order": order}
    except Exception as e:
        log.error("Trade failed: %s", e)
        return {"status": "error", "detail": str(e)}

# ---------- Routes ----------
@app.get("/")
async def root():
    return {"status": "NIJA Trading Bot LIVE"}

@app.post("/webhook")
async def webhook(signal: TradeSignal, request: Request):
    """Receives TradingView webhook signals and executes trades live."""
    log.info("Webhook received: %s", signal.dict())
    result = safe_execute_trade(signal.symbol, signal.action, signal.size)
    return result

# ---------- Run Server ----------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
