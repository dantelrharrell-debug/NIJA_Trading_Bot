# ------------------------------
# Nija Bot Live Deployment Version - Corrected .env Handling
# ------------------------------

import os
import time
from coinbase.wallet.client import Client
from dotenv import load_dotenv

# ------------------------------
# 1️⃣ Load environment variables
# ------------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET not found. Please set them in your .env file.")

# ------------------------------
# 2️⃣ Initialize Coinbase client
# ------------------------------
client = Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized successfully!")

# ------------------------------
# 3️⃣ Minimum trade amounts per ticker
# ------------------------------
coinbase_min = {
    "BTCUSD": 10,
    "ETHUSD": 1,
    "LTCUSD": 1,
    "SOLUSD": 1,
    "DOGEUSD": 1,
    "XRPUSD": 1,
    "BTCFUT": 10,    # Example BTC Futures minimum
    "ETHFUT": 10     # Example ETH Futures minimum
}

# Priority order: Futures first, then BTC, then altcoins
priority_order = ["BTCFUT", "ETHFUT", "BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD", "DOGEUSD", "XRPUSD"]

# ------------------------------
# 4️⃣ Dynamic allocation function
# ------------------------------
def allocate_dynamic(balance_fetcher, min_trade, priority):
    total_balance = balance_fetcher()
    allocations = {asset: 0 for asset in min_trade.keys()}
    
    # Assign minimums to priority assets
    for asset in priority:
        if total_balance >= min_trade[asset]:
            allocations[asset] = min_trade[asset]
            total_balance -= min_trade[asset]
        else:
            allocations[asset] = 0

    # Distribute leftover balance evenly among trading assets
    trading_assets = [a for a, amt in allocations.items() if amt >= min_trade[a]]
    if trading_assets and total_balance > 0:
        per_asset_extra = total_balance / len(trading_assets)
        for a in trading_assets:
            allocations[a] += per_asset_extra

    # Ensure allocations meet minimums
    for a in allocations:
        if 0 < allocations[a] < min_trade[a]:
            allocations[a] = 0

    return allocations

# ------------------------------
# 5️⃣ Get current USD balance
# ------------------------------
def get_current_balance():
    try:
        account = client.get_account("USD")
        return float(account.balance.amount)
    except Exception as e:
        print(f"Error fetching USD balance: {e}")
        return 0

# ------------------------------
# 6️⃣ Trade execution function
# ------------------------------
def execute_trade(asset, side="buy"):
    dynamic_allocations = allocate_dynamic(get_current_balance, coinbase_min, priority_order)
    trade_amount = dynamic_allocations.get(asset, 0)
    
    if trade_amount <= 0:
        print(f"Skipped {asset}: allocation below minimum.")
        return

    try:
        order = client.place_order(
            product_id=asset,
            side=side,
            order_type="market",
            size=trade_amount
        )
        print(f"✅ Placed {side} order for {asset} with amount ${trade_amount}")
    except Exception as e:
        print(f"❌ Error placing order for {asset}: {e}")

# ------------------------------
# 7️⃣ Example Trading Loop / Signal Handling
# ------------------------------
# Replace this loop with your TradingView webhook integration
assets_to_trade = ["BTCUSD","ETHUSD","LTCUSD","SOLUSD","DOGEUSD","XRPUSD"]  # Example assets

while True:
    for asset in assets_to_trade:
        execute_trade(asset, side="buy")  # Replace with logic from TradingView signals
    print("Waiting 60 seconds for next trading cycle...")
    time.sleep(60)
