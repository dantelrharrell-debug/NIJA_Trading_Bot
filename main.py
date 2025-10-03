from fastapi import FastAPI
import os
import time
import threading
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

# Settings
TRADE_INTERVAL = 180  # seconds (3 minutes)
MIN_BALANCE = 10      # minimum USD balance to trade
SYMBOLS = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD"]  # trading pairs

def trade_loop():
    while True:
        try:
            usd_balance = client.get_account("USD")["available"]
            if float(usd_balance) < MIN_BALANCE:
                print(f"Skipping trades: USD balance below minimum ({usd_balance})")
            else:
                for symbol in SYMBOLS:
                    try:
                        # Example simple strategy: market buy $10 per symbol
                        order = client.place_market_order(
                            symbol=symbol,
                            side="buy",
                            size=10,  # USD amount
                            product_type="spot"
                        )
                        print(f"Executed trade: {order}")
                    except Exception as e:
                        print(f"Trade failed for {symbol}: {e}")
        except Exception as e:
            print(f"Error fetching USD balance: {e}")
        time.sleep(TRADE_INTERVAL)

# Start trading in background thread
threading.Thread(target=trade_loop, daemon=True).start()

@app.get("/")
def root():
    return {"status": "ok", "message": "NIJA Trading Bot is live and trading!"}

@app.get("/check-coinbase")
def check_coinbase():
    return {"status": "ok", "message": coinbase_status}

@app.get("/balance")
def get_balance():
    try:
        balance = client.get_account("USD")["available"]
        return {"status": "ok", "USD_available": balance}
    except Exception as e:
        return {"status": "error", "message": str(e)}
