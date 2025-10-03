import os
import asyncio
from fastapi import FastAPI
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load API keys
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize Coinbase client
try:
    client = Client(API_KEY, API_SECRET)
    print("Coinbase client initialized successfully.")
except Exception as e:
    print("Coinbase client failed:", e)
    client = None

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Bot running", "coinbase_client": bool(client)}

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
        print("No client. Skipping trading loop.")
        return
    while True:
        try:
            print("Balance:", client.get_usd_balance())
            # TODO: Place real trading orders here
            await asyncio.sleep(10)
        except Exception as e:
            print("Trading loop error:", e)
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_loop())
