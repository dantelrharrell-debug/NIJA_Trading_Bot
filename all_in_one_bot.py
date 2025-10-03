import os
import asyncio
from fastapi import FastAPI
from coinbase_advanced_py import Client
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

try:
    client = Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None  # Run in diagnostic mode

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

# Example autonomous trading loop
async def trading_loop():
    if not client:
        print("Coinbase client not initialized. Exiting trading loop.")
        return

    while True:
        try:
            # Example: fetch balance
            balance = client.get_usd_balance()
            print("USD Balance:", balance)

            # TODO: add real trading logic here
            # Example: client.place_order("BTC-USD", "buy", amount)

            await asyncio.sleep(10)  # Run every 10 seconds
        except Exception as e:
            print("Error in trading loop:", e)
            await asyncio.sleep(10)

# Start trading loop when app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_loop())
