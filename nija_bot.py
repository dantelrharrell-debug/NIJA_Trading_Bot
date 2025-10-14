#!/usr/bin/env python3
# main.py / nija_bot.py - NIJA BOT fully live

import os
import sys
import json
import traceback
from coinbase import Client

# ---------- Environment & API Setup ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables")

client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized successfully")

# ---------- Config ----------
MIN_ALLOCATION = 0.02  # 2%
MAX_ALLOCATION = 0.10  # 10%
TRADE_SYMBOLS = ["BTC", "ETH"]  # Add more if needed

# ---------- Helper Functions ----------
def print_balances():
    """Fetch and print all account balances"""
    try:
        balances = client.get_account_balances()
        print("💰 Account Balances:")
        for account in balances:
            print(f"  {account['currency']}: {account['balance']}")
        return balances
    except Exception as e:
        print("❌ Error fetching balances:", e)
        traceback.print_exc()
        return []

def get_account_equity(balances):
    """Return total USD-equivalent account equity"""
    total = 0
    try:
        for account in balances:
            # Use USD balance directly
            if account['currency'] == "USD":
                total += float(account['balance'])
            else:
                # Convert crypto balance to USD
                price = client.get_spot_price(account['currency'])
                total += float(account['balance']) * float(price['amount'])
    except Exception as e:
        print("❌ Error calculating equity:", e)
        traceback.print_exc()
    return total

def calculate_trade_amount(equity, allocation_percent, price):
    """Determine trade amount based on allocation rules"""
    allocation_percent = max(MIN_ALLOCATION, min(MAX_ALLOCATION, allocation_percent))
    usd_amount = equity * allocation_percent
    crypto_amount = usd_amount / price
    return round(crypto_amount, 8)

def place_trade(symbol, side, allocation_percent=0.05):
    """Place a live trade with dynamic sizing"""
    try:
        balances = print_balances()
        equity = get_account_equity(balances)
        price = float(client.get_spot_price(symbol)['amount'])
        amount = calculate_trade_amount(equity, allocation_percent, price)

        print(f"⚡ Placing {side.upper()} order for {symbol}: {amount} (~{allocation_percent*100}% of equity)")
        order = client.place_order(
            symbol=symbol,
            side=side,
            type="market",
            amount=str(amount)
        )
        print("✅ Order executed:", order)
    except Exception as e:
        print("❌ Trade failed:", e)
        traceback.print_exc()

# ---------- Main Bot Logic ----------
if __name__ == "__main__":
    print("🌟 NIJA BOT starting...")
    print("Python executable:", sys.executable)
    print("sys.path:", sys.path)

    # Test balances
    print_balances()

    # Example trades
    for symbol in TRADE_SYMBOLS:
        place_trade(symbol, "buy", allocation_percent=0.05)

    print("🔥 Bot running. Ready for live trades!")
