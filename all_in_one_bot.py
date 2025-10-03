# all_in_one_bot.py

import os
import time
import threading
import subprocess
import sys
from fastapi import FastAPI
from dotenv import load_dotenv

# ----------------------
# Ensure coinbase_advanced_py is installed
# ----------------------
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("coinbase_advanced_py not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py"])
    import coinbase_advanced_py as cb

# ----------------------
# Load environment vars
# ----------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTC-USD")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "10"))
PRICE_CHECK_INTERVAL = float(os.getenv("PRICE_CHECK_INTERVAL", "10"))

# ----------------------
# Initialize Coinbase Client
# ----------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None

# ----------------------
# FastAPI Setup
# ----------------------
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot running", "coinbase_client": bool(client)}

@app.get("/balance")
async def balance():
    if client:
        try:
            usd_balance = client.get_usd_balance()
            return {"USD_balance": usd_balance}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Coinbase client not initialized"}

@app.get("/position")
async def position():
    if client:
        try:
            positions = client.get_positions()
            return {"positions": positions}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Coinbase client not initialized"}

# ----------------------
# Simple Autonomous Trading Loop
# ----------------------
def trading_loop():
    if not client:
        print("Coinbase client not initialized. Trading loop stopped.")
        return

    last_price = None
    while True:
        try:
            current_price = client.get_price(TRADE_SYMBOL)
            print(f"[{TRADE_SYMBOL}] Current Price: {current_price}")

            if last_price is None:
                last_price = current_price
                time.sleep(PRICE_CHECK_INTERVAL)
                continue

            change_percent = ((current_price - last_price) / last_price) * 100

            if change_percent <= -0.5:
                order = client.place_order(symbol=TRADE_SYMBOL, side="buy", amount=TRADE_AMOUNT)
                print(f"Bought ${TRADE_AMOUNT} {TRADE_SYMBOL} at {current_price}")
                last_price = current_price
            elif change_percent >= 0.5:
                order = client.place_order(symbol=TRADE_SYMBOL, side="sell", amount=TRADE_AMOUNT)
                print(f"Sold ${TRADE_AMOUNT} {TRADE_SYMBOL} at {current_price}")
                last_price = current_price

        except Exception as e:
            print("Error in trading loop:", e)

        time.sleep(PRICE_CHECK_INTERVAL)

# Run trading loop in background thread
threading.Thread(target=trading_loop, daemon=True).start()
