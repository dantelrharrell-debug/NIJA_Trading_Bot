from fastapi import FastAPI
import os
import coinbase_advanced_py as cb
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NIJA Trading Bot")

# Initialize Coinbase Advanced client
try:
    client = cb.Client(
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET")
    )
    coinbase_status = "Coinbase Advanced client initialized!"
except Exception as e:
    coinbase_status = f"Coinbase init failed: {str(e)}"

@app.get("/")
def root():
    return {"status": "ok", "message": "NIJA Trading Bot is live!"}

@app.get("/check-coinbase")
def check_coinbase():
    return {"status": "ok", "message": coinbase_status}
