# main.py

import os
import time
import random
from coinbase_advanced_py import CoinbaseAdvanced
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------
# API Credentials
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# -----------------------------
# Risk Settings (AI adjustable)
# -----------------------------
MIN_RISK_PERCENT = 2    # Minimum 2%
MAX_RISK_PERCENT = 10   # Maximum 10%

# -----------------------------
# Symbols to trade
# -----------------------------
SYMBOLS = ["BTC-USD", "ETH-USD"]  # add more if needed

# -----------------------------
# Initialize Coinbase Advanced client
# -----------------------------
cb = CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)

# -----------------------------
# Helper functions
# -----------------------------
def get_account_balance():
    """Return total USD balance available."""
    accounts = cb.get_accounts()
    for account in accounts:
        if account['currency'] == "USD":
            return float(account['balance'])
    return 0.0

def ai_adjust_risk():
    """AI dynamically adjusts risk between MIN and MAX."""
    # Replace this with real AI logic if desired
    return round(random.uniform(MIN_RISK_PERCENT, MAX_RISK_PERCENT), 2)

def calculate_position_size(balance, risk_percent):
    """Calculate how much USD to risk for this trade."""
    return round(balance * (risk_percent / 100), 2)

def execute_trade(symbol, side="buy"):
    """Place a trade with risk management."""
    try:
        balance = get_account_balance()
        if balance <= 0:
            print("No USD balance to trade. Waiting...")
            return

        risk = ai_adjust_risk()
        size = calculate_position_size(balance, risk)

        print(f"Placing {side.upper()} trade on {symbol} | Risk: {risk}% | USD Size: ${size}")

        # Execute the trade
        cb.place_order(symbol=symbol, side=side, size=size, type="market")
        print(f"Trade executed ✅ {symbol} {side} ${size}")

    except Exception as e:
        print(f"Trade error: {e}")

# -----------------------------
# Main live trading loop
# -----------------------------
def live_trading_loop():
    print("Nija AI Trading Bot is LIVE ✅")
    while True:
        for symbol in SYMBOLS:
            # Alternate buy/sell for demonstration
            side = "buy" if random.random() > 0.5 else "sell"
            execute_trade(symbol, side)
        time.sleep(10)  # Adjust frequency as needed

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    live_trading_loop()
