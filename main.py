from fastapi import FastAPI
import coinbase_advanced_py as cb
from dotenv import load_dotenv
import os
import datetime
import threading
import time

load_dotenv()

app = FastAPI(title="NIJA Trading Bot Dashboard")

# Initialize Coinbase client
try:
    client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    coinbase_status = "Coinbase client initialized!"
except Exception as e:
    coinbase_status = f"Coinbase init failed: {str(e)}"

# Global storage for dashboard
dashboard = {
    "balances": {},
    "positions": {},
    "last_trades": {},
    "indicators": {}
}

# Dummy coin list
coins = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD"]

def calculate_vwap_rsi(prices):
    # Simplified calculation placeholders
    vwap = sum(prices) / len(prices)
    rsi = 50  # Replace with actual RSI calculation if desired
    return vwap, rsi

def trade_loop():
    while True:
        for coin in coins:
            try:
                # Fetch latest prices
                ticker = client.get_spot_price(currency_pair=coin)
                price = float(ticker.amount)
                
                # Update indicators
                vwap, rsi = calculate_vwap_rsi([price]*14)  # placeholder 14 bars
                dashboard["indicators"][coin] = {"vwap": vwap, "rsi": rsi}

                # Simple trade logic
                if price > vwap and rsi < 30:
                    action = "BUY"
                elif price < vwap and rsi > 70:
                    action = "SELL"
                else:
                    action = "HOLD"

                # Record last trade
                dashboard["last_trades"][coin] = {
                    "action": action,
                    "price": price,
                    "time": datetime.datetime.utcnow().isoformat()
                }

                # Update balances (mock or fetch real)
                dashboard["balances"][coin] = price * 1  # Replace with actual balance fetch
                dashboard["positions"][coin] = action

            except Exception as e:
                print(f"Error processing {coin}: {e}")

        time.sleep(180)  # 3 minutes loop

# Run trade loop in a separate thread
threading.Thread(target=trade_loop, daemon=True).start()

@app.get("/")
def root():
    return {"status": "ok", "message": "NIJA Trading Bot is live!"}

@app.get("/check-coinbase")
def check_coinbase():
    return {"status": "ok", "message": coinbase_status}

@app.get("/dashboard")
def get_dashboard():
    return dashboard
