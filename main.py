# main.py (All-in-One Nija Trading Bot)
import os
import logging
from fastapi import FastAPI, Request
from pydantic import BaseModel
from coinbase_advanced_py import Client
import uvicorn

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("nija_trading_bot")

# ---------- Load Environment ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    log.error("API_KEY or API_SECRET not set in environment variables.")
    raise EnvironmentError("API_KEY and API_SECRET must be set in .env")

# ---------- Coinbase Client ----------
try:
    coinbase_client = Client(API_KEY, API_SECRET)
    log.info("Coinbase client successfully initialized.")
except Exception as e:
    coinbase_client = None
    log.error("Failed to initialize Coinbase client: %s", e)
    raise e

# ---------- FastAPI Setup ----------
app = FastAPI(title="NIJA Trading Bot Webhook")

# ---------- Pydantic Model ----------
class TradeSignal(BaseModel):
    symbol: str
    action: str  # "buy" or "sell"
    size: float  # quantity to trade

# ---------- Routes ----------
@app.get("/")
async def root():
    return {"status": "NIJA Trading Bot is live!"}

@app.post("/webhook")
async def webhook(signal: TradeSignal, request: Request):
    if coinbase_client is None:
        log.warning("Webhook received but Coinbase client not initialized!")
        return {"status": "error", "detail": "Coinbase client not initialized"}
    
    log.info("Webhook received: %s", signal.dict())
    
    try:
        if signal.action.lower() == "buy":
            order = coinbase_client.place_market_order(
                product_id=f"{signal.symbol}-USD",
                side="buy",
                funds=str(signal.size)  # Using funds in USD
            )
            log.info("Buy order executed: %s", order)
        elif signal.action.lower() == "sell":
            order = coinbase_client.place_market_order(
                product_id=f"{signal.symbol}-USD",
                side="sell",
                size=str(signal.size)  # Selling a crypto amount
            )
            log.info("Sell order executed: %s", order)
        else:
            log.warning("Unknown action: %s", signal.action)
            return {"status": "error", "detail": "Unknown action"}
        
        return {"status": "success", "order": order}
    except Exception as e:
        log.error("Failed to execute trade: %s", e)
        return {"status": "error", "detail": str(e)}

# ---------- Uvicorn Entry ----------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
