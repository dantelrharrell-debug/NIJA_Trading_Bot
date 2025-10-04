#!/usr/bin/env python3
import importlib.util
import subprocess
import sys
import logging
import os
from fastapi import FastAPI, Request
import json

# ===========================
# Logging setup
# ===========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ===========================
# Ensure required modules
# ===========================
def ensure_modules():
    modules = {
        "coinbase_advanced_py": "coinbase-advanced-py",
        "coinbase.wallet.client": "coinbase"
    }
    for mod_name, pip_name in modules.items():
        if importlib.util.find_spec(mod_name) is None:
            logging.warning(f"Module '{mod_name}' not found. Installing '{pip_name}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        else:
            logging.info(f"Module '{mod_name}' found.")

ensure_modules()

# ===========================
# Import Coinbase Clients
# ===========================
try:
    from coinbase_advanced_py import Client as AdvancedClient
    logging.info("✅ coinbase_advanced_py imported successfully")
except ImportError:
    logging.error("❌ Failed to import coinbase_advanced_py")
    AdvancedClient = None

try:
    from coinbase.wallet.client import Client as WalletClient
    logging.info("✅ coinbase.wallet.client imported successfully")
except ImportError:
    logging.warning("⚠️ coinbase.wallet.client not available (optional)")
    WalletClient = None

# ===========================
# Load API keys
# ===========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    logging.error("❌ API_KEY or API_SECRET not set in environment")
    client = None
else:
    try:
        client = AdvancedClient(API_KEY, API_SECRET)
        logging.info("✅ Coinbase Advanced client initialized")
    except Exception as e:
        logging.error(f"❌ Failed to initialize client: {e}")
        client = None

# ===========================
# FastAPI app
# ===========================
app = FastAPI()

@app.get("/")
def root():
    return {"status": "NIJA Trading Bot is live 🚀"}

# ===========================
# Webhook endpoint for TradingView signals
# ===========================
@app.post("/webhook")
async def webhook(request: Request):
    if not client:
        logging.warning("⚠️ Webhook received but client not initialized")
        return {"status": "diagnostic mode, no trade executed"}

    try:
        data = await request.json()
        logging.info(f"Webhook data received: {json.dumps(data)}")

        # Example: structure expected {"symbol": "BTC-USD", "action": "buy", "size": 0.01}
        symbol = data.get("symbol")
        action = data.get("action")
        size = data.get("size")

        if symbol and action and size:
            logging.info(f"Executing {action.upper()} {size} {symbol}")
            # Execute order
            if action.lower() == "buy":
                result = client.place_order(
                    product_id=symbol,
                    side="buy",
                    type="market",
                    size=size
                )
            elif action.lower() == "sell":
                result = client.place_order(
                    product_id=symbol,
                    side="sell",
                    type="market",
                    size=size
                )
            else:
                logging.error(f"Invalid action: {action}")
                return {"status": "error", "message": "Invalid action"}

            logging.info(f"Order executed: {result}")
            return {"status": "success", "order": result}

        else:
            logging.error("Invalid webhook payload")
            return {"status": "error", "message": "Invalid payload"}

    except Exception as e:
        logging.error(f"Exception in webhook: {e}")
        return {"status": "error", "message": str(e)}

# ===========================
# Fetch balances on startup
# ===========================
if client:
    try:
        accounts = client.get_accounts()
        logging.info(f"Accounts fetched: {accounts}")
    except Exception as e:
        logging.error(f"Failed to fetch accounts: {e}")

# ===========================
# Run Uvicorn if executed directly
# ===========================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
