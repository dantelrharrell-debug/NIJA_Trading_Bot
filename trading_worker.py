#!/usr/bin/env python3
import os
import sys
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

# Coinbase credentials
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE", "")

if not (API_KEY and API_SECRET):
    print("❌ Missing API credentials. Exiting.")
    sys.exit(1)

# Import Coinbase clients
try:
    from coinbase.rest import CoinbaseRESTClient
    from coinbase.websocket import CoinbaseWebsocketClient
    print("✅ Coinbase clients imported successfully.")
except Exception as e:
    print("❌ Failed to import Coinbase clients:")
    traceback.print_exc()
    sys.exit(1)

# -------------------
# Initialize clients
# -------------------
try:
    if USE_MOCK:
        print("⚡ Running in MOCK mode (no live trades).")
        rest_client = None
        ws_client = None
    else:
        rest_client = CoinbaseRESTClient(API_KEY, API_SECRET)
        ws_client = CoinbaseWebsocketClient(API_KEY, API_SECRET)
        print("✅ Coinbase clients initialized successfully.")
except Exception as e:
    print("❌ Failed to initialize Coinbase clients:")
    traceback.print_exc()
    sys.exit(1)

# -------------------
# Safe position sizing
# -------------------
def get_trade_size(account_balance, pct_min=2, pct_max=10):
    """Returns trade size in USD based on account equity."""
    trade_pct = max(pct_min, min(pct_max, 5))  # default 5%, adjust as needed
    return account_balance * trade_pct / 100

# -------------------
# Trading signals (placeholders)
# -------------------
def check_vwap_signal():
    # Replace with real VWAP logic
    return "BUY"

def check_rsi_signal():
    # Replace with real RSI logic
    return "SELL"

# -------------------
# Main trading loop
# -------------------
def main():
    print("🚀 Trading worker started at", datetime.now())
    while True:
        try:
            if USE_MOCK:
                print(f"{datetime.now()} | MOCK trade check: VWAP={check_vwap_signal()} RSI={check_rsi_signal()}")
            else:
                # Fetch balances
                accounts = rest_client.get_accounts()
                for acc in accounts:
                    balance = float(acc['balance']['amount'])
                    trade_size = get_trade_size(balance)
                    print(f"{datetime.now()} | {acc['currency']} balance: {balance}, suggested trade: {trade_size}")

                # Example: use signals
                vwap_signal = check_vwap_signal()
                rsi_signal = check_rsi_signal()
                print(f"{datetime.now()} | Signals: VWAP={vwap_signal}, RSI={rsi_signal}")

            time.sleep(5)  # Poll every 5 seconds, adjust as needed

        except KeyboardInterrupt:
            print("✋ Worker stopped manually.")
            break
        except Exception:
            print("⚠️ Error in trading loop:")
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
