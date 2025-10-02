# ------------------------------
# Nija Trading Bot - Deploy Ready
# ------------------------------

import os
import time
from coinbase.wallet.client import Client
from dotenv import load_dotenv

# ------------------------------
# Load API keys
# ------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET not found in .env file.")

client = Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized successfully!")

# ------------------------------
# Minimum trade amounts & priority order
# ------------------------------
coinbase_min = {
    "BTCUSD": 10,
    "ETHUSD": 1,
    "LTCUSD": 1,
    "SOLUSD": 1,
    "DOGEUSD": 1,
    "XRPUSD": 1,
    "BTCFUT": 10,    # Example Futures minimum
    "ETHFUT": 10
}

priority_order = ["BTCFUT", "ETHFUT", "BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD", "DOGEUSD", "XRPUSD"]

# ------------------------------
# Dynamic allocation function
# ------------------------------
def allocate_dynamic(balance_fetcher, min_trade, priority):
    total_balance = balance_fetcher()
    allocations = {asset: 0 for asset in min_trade.keys()}

    # Assign minimums to priority assets
    for asset in priority:
        if total_balance >= min_trade[asset]:
            allocations[asset] = min_trade[asset]
            total_balance -= min_trade[asset]

    # Distribute leftover balance evenly
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
# Get live USD balance
# ------------------------------
def get_current_balance():
    try:
        account = client.get_account("USD")
        return float(account.balance.amount)
    except Exception as e:
        print(f"Error fetching USD balance: {e}")
        return 0

# ------------------------------
# Execute a trade
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
# Example Trading Loop (replace with TradingView signals)
# ------------------------------
assets_to_trade = ["BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD", "DOGEUSD", "XRPUSD"]

while True:
    for asset in assets_to_trade:
        execute_trade(asset)
    print("Waiting 60 seconds for next cycle...")
    time.sleep(60)
