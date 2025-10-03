# all_in_one_bot.py
import os
import sys
import subprocess
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

# =========================
# Dynamic installation of Coinbase Advanced
# =========================
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("coinbase_advanced_py not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py"])
    import coinbase_advanced_py as cb
    print("coinbase_advanced_py installed successfully.")

# =========================
# Load environment variables
# =========================
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# =========================
# Initialize Coinbase Advanced client
# =========================
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None  # Bot will run in diagnostic mode

# =========================
# Initialize FastAPI
# =========================
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot is running...", "coinbase_client": bool(client)}

@app.get("/balance")
async def balance():
    if client:
        try:
            return {"USD_balance": client.get_usd_balance()}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Coinbase client not initialized."}

# =========================
# Autonomous trading logic (basic example)
# =========================
async def trading_loop():
    if not client:
        print("Coinbase client not initialized. Trading loop will not run.")
        return
    print("Starting autonomous trading loop...")
    while True:
        try:
            # Example: check balance and place a sample order
            usd_balance = client.get_usd_balance()
            print(f"USD balance: {usd_balance}")

            # Example: Place a tiny test order if balance > 10 USD
            if usd_balance > 10:
                order = client.place_order(
                    symbol="BTC-USD",
                    side="buy",
                    type="market",
                    quantity=0.001  # adjust to your needs
                )
                print(f"Placed order: {order}")

            await asyncio.sleep(60)  # check/trade every 60 seconds
        except Exception as e:
            print("Error in trading loop:", e)
            await asyncio.sleep(60)

# =========================
# Run trading loop in background when FastAPI starts
# =========================
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_loop())

# =========================
# To run locally: uvicorn all_in_one_bot:app --host 0.0.0.0 --port 8080
# =========================
