#!/#!/usr/bin/env python3
import os
import sys
import time
import traceback
from coinbase_advanced_py import Coinbase  # ✅ new live client import

from dotenv import load_dotenv
load_dotenv()  # load API keys from .env

# ------------------------
# Load API keys from env
# ------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PASSPHRASE = os.getenv("PASSPHRASE")  # if required by your setup

if not API_KEY or not API_SECRET:
    print("❌ Missing API_KEY or API_SECRET in environment.")
    sys.exit(1)

# ------------------------
# Initialize live client
# ------------------------
try:
    client = Coinbase(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ Coinbase client initialized successfully (live mode).")
except Exception as e:
    print("❌ Failed to initialize Coinbase client:", e)
    traceback.print_exc()
    sys.exit(1)

# ------------------------
# Main trading loop
# ------------------------
def main():
    print("🚀 Trading worker running...")
    while True:
        try:
            # Example: get BTC-USD price
            ticker = client.rest.get_ticker("BTC-USD")
            price = ticker["price"]
            print(f"[{time.strftime('%H:%M:%S')}] BTC-USD price: {price}")
            
            # TODO: add your live trading logic here
            time.sleep(5)  # adjust frequency
        except KeyboardInterrupt:
            print("✋ Stopping trading worker...")
            break
        except Exception as e:
            print("⚠️ Error in trading loop:", e)
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
