# main.py
import os
from fastapi import FastAPI
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load environment variables
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

# Initialize FastAPI
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
