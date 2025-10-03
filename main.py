import os
import time
import threading
from fastapi import FastAPI
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize Coinbase Advanced client
try:
    client = Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None  # Bot will run in diagnostic mode

# FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot is running", "coinbase_client": bool(client)}

@app.get("/balance")
async def balance():
    if client:
        try:
            usd_balance = client.get_usd_balance()
            return {"USD_balance": usd_balance}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Coinbase client not initialized."}

# -----------------------------
# Basic Auto-Trading Loop
# -----------------------------
def trade_loop():
    if not client:
        print("Client not initialized. Skipping trading loop.")
        return

    while True:
        try:
            # Example: Buy 0.001 BTC if USD balance > 10
            usd_balance = client.get_usd_balance()
            print("USD Balance:", usd_balance)

            if usd_balance >= 10:
                print("Placing a test BTC buy for $10")
                client.place_market_order(symbol="BTC-USD", side="buy", usd_amount=10)

            time.sleep(60)  # wait 1 minute before next check
        except Exception as e:
            print("Error in trade loop:", e)
            time.sleep(60)

# Run trading loop in background thread
threading.Thread(target=trade_loop, daemon=True).start()
