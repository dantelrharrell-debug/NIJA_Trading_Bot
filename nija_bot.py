#!/usr/bin/env python3
# nija_bot.py - Nija Trading Bot (Web Service + Live Trading Ready)

import os
import sys
import time
import json
import traceback
from coinbase_advanced_py import Client  # ✅ Fixed import

# -----------------------
# Environment Variables
# -----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

# -----------------------
# Coinbase Client
# -----------------------
client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized successfully")

# -----------------------
# Bot Config
# -----------------------
MIN_ALLOCATION = 0.02
MAX_ALLOCATION = 0.10
TRADE_SYMBOLS = ["BTC", "ETH"]
SLEEP_SECONDS = 60
BASE_COOLDOWN = 300
TRADE_LOG = "trades.json"
TRADE_HISTORY_COUNT = 5

last_trade_time = {symbol: 0 for symbol in TRADE_SYMBOLS}

# -----------------------
# Helper Functions
# -----------------------
def print_balances():
    try:
        balances = client.get_account_balances()
        for account in balances:
            print(f"💰 {account['currency']}: {account['balance']}")
        return balances
    except Exception as e:
        print("❌ Error fetching balances:", e)
        traceback.print_exc()
        return []

def get_account_equity(balances):
    total = 0
    try:
        for account in balances:
            if account['currency'] == "USD":
                total += float(account['balance'])
            else:
                price = float(client.get_spot_price(account['currency'])['amount'])
                total += float(account['balance']) * price
    except Exception as e:
        print("❌ Error calculating equity:", e)
        traceback.print_exc()
    return total

def calculate_trade_amount(equity, allocation_percent, price):
    allocation_percent = max(MIN_ALLOCATION, min(MAX_ALLOCATION, allocation_percent))
    usd_amount = equity * allocation_percent
    return round(usd_amount / price, 8)

def get_rsi(symbol, period=14):
    try:
        candles = client.get_historic_rates(symbol, granularity=60)
        closes = [float(c[4]) for c in candles[-(period+1):]]
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            gains.append(max(diff, 0))
            losses.append(abs(min(diff, 0)))
        avg_gain, avg_loss = sum(gains)/period, sum(losses)/period
        return 100 - (100 / (1 + avg_gain / (avg_loss or 1e-6)))
    except:
        return 50

def get_vwap(symbol, period=20):
    try:
        candles = client.get_historic_rates(symbol, granularity=60)
        closes = [float(c[4]) for c in candles[-period:]]
        volumes = [float(c[5]) for c in candles[-period:]]
        return sum(c*v for c,v in zip(closes, volumes))/sum(volumes)
    except:
        return float(client.get_spot_price(symbol)['amount'])

def get_volatility(symbol, period=20):
    try:
        candles = client.get_historic_rates(symbol, granularity=60)
        closes = [float(c[4]) for c in candles[-period:]]
        mean = sum(closes)/len(closes)
        variance = sum((p - mean)**2 for p in closes)/len(closes)
        return variance**0.5
    except:
        return 0

def load_trade_history():
    history = {}
    if os.path.exists(TRADE_LOG):
        with open(TRADE_LOG, "r") as f:
            for line in f:
                try:
                    t = json.loads(line)
                    history.setdefault(t["symbol"], []).append(t)
                except:
                    continue
    return history

def adjust_allocation(symbol, base_percent):
    history = load_trade_history().get(symbol, [])[-TRADE_HISTORY_COUNT:]
    if not history:
        return base_percent
    profit_factor = sum(t.get("profit",0) for t in history)/TRADE_HISTORY_COUNT
    allocation = base_percent + (profit_factor*0.5)
    volatility = get_volatility(symbol)
    allocation = allocation / (1 + volatility)
    return max(MIN_ALLOCATION, min(MAX_ALLOCATION, allocation))

def can_trade(symbol):
    return time.time() - last_trade_time[symbol] > BASE_COOLDOWN

def place_trade(symbol, side, base_allocation=0.05):
    try:
        balances = print_balances()
        equity = get_account_equity(balances)
        price = float(client.get_spot_price(symbol)['amount'])
        allocation = adjust_allocation(symbol, base_allocation)
        amount = calculate_trade_amount(equity, allocation, price)

        if not can_trade(symbol):
            print(f"⏳ Cooldown active for {symbol}, skipping trade")
            return

        print(f"⚡ Placing {side.upper()} for {symbol}: {amount} (~{allocation*100:.1f}% equity)")
        if LIVE_TRADING:
            order = client.place_order(symbol=symbol, side=side, type="market", amount=str(amount))
        last_trade_time[symbol] = time.time()

        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps({"symbol":symbol,"side":side,"amount":amount,"price":price,"timestamp":time.time()})+"\n")
        print("✅ Trade executed and logged")
    except Exception as e:
        print("❌ Trade failed:", e)
        traceback.print_exc()

# -----------------------
# Main Loop
# -----------------------
if __name__ == "__main__":
    print("🌟 NIJA BOT Self-Optimizing Loop Starting")
    while True:
        try:
            balances = print_balances()
            equity = get_account_equity(balances)
            print(f"💵 Total Equity: ${equity:.2f}")

            for symbol in TRADE_SYMBOLS:
                rsi = get_rsi(symbol)
                vwap = get_vwap(symbol)
                price = float(client.get_spot_price(symbol)['amount'])
                print(f"📊 {symbol} RSI:{rsi:.2f} Price:{price:.2f} VWAP:{vwap:.2f}")

                if price < vwap and rsi < 30:
                    place_trade(symbol, "buy")
                elif price > vwap and rsi > 70:
                    place_trade(symbol, "sell")
                else:
                    print(f"ℹ️ No signal for {symbol}")

        except Exception as e:
            print("❌ Main loop error:", e)
            traceback.print_exc()

        print(f"⏳ Sleeping {SLEEP_SECONDS}s before next cycle\n")
        time.sleep(SLEEP_SECONDS)
