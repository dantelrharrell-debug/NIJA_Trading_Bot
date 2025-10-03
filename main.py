# main.py
import os
import time
import threading
from fastapi import FastAPI
from dotenv import load_dotenv

# Try to import Coinbase client, install if missing
try:
    from coinbase_advanced_py import Client
except ModuleNotFoundError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py"])
    from coinbase_advanced_py import Client

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize Coinbase client
try:
    client = Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None

# FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot is running...", "coinbase_client": bool(client)}

@app.get("/balance")
async def balance():
    if client:
        try:
            usd_balance = client.get_usd_balance()
            return {"USD_balance": usd_balance}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Coinbase client not initialized."}

# -------- Auto-Trading Loop --------
def auto_trade():
    if not client:
        print("Coinbase client not initialized. Auto-trading disabled.")
        return

    while True:
        try:
            usd_balance = client.get_usd_balance()
            print(f"USD Balance: {usd_balance}")

            if usd_balance > 10:
                test_order = client.place_order(
                    symbol="BTC-USD",
                    side="buy",
                    type="market",
                    funds="5"
                )
                print("Placed test order:", test_order)

            time.sleep(60)
        except Exception as e:
            print("Error in trading loop:", e)
            time.sleep(60)

# Start auto-trading in a background thread
if client:
    threading.Thread(target=auto_trade, daemon=True).start()
