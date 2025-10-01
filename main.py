# main.py
import os
import time
from coinbase_advanced_py import CoinbaseAdvanced
import numpy as np

# -------------------------
# === API KEYS ============
# -------------------------
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

# Initialize Coinbase Advanced client
client = CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)

# -------------------------
# === RISK PARAMETERS =====
# -------------------------
MIN_RISK = 0.02  # 2%
MAX_RISK = 0.10  # 10%

# -------------------------
# === TRADE PARAMETERS ====
# -------------------------
MIN_TRADE = 10.0  # minimum $ trade amount
STOP_LOSS_PERCENT = 0.03  # 3%
TAKE_PROFIT_PERCENT = 0.05  # 5%

# -------------------------
# === MARKET LOGIC =========
# -------------------------
def calculate_risk(balance):
    """Adaptive risk between MIN_RISK and MAX_RISK"""
    # Example: simple volatility-based risk adjustment
    risk = np.random.uniform(MIN_RISK, MAX_RISK)
    trade_amount = balance * risk
    return max(trade_amount, MIN_TRADE)

def determine_trade_signal():
    """
    Simple AI placeholder for Bull/Bear bias
    Returns: 'buy', 'sell', or 'hold'
    """
    # Replace with your AI logic
    bias = np.random.choice(['buy', 'sell', 'hold'], p=[0.4, 0.4, 0.2])
    return bias

# -------------------------
# === PLACE ORDER ==========
# -------------------------
def place_order(symbol: str, side: str, quantity: float):
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            size=quantity,
            order_type='market'
        )
        print(f"[✅] {side.upper()} order placed for {quantity} {symbol}. ID: {order['id']}")
        return order
    except Exception as e:
        print(f"[❌] Failed to place order: {e}")

# -------------------------
# === MAIN LOOP ===========
# -------------------------
def main():
    symbol = "BTC-USD"  # Change to your trading pair
    balance = float(client.get_account_balance(symbol.split('-')[1]))  # e.g., USD balance
    
    while True:
        signal = determine_trade_signal()
        if signal in ['buy', 'sell']:
            trade_amount = calculate_risk(balance)
            place_order(symbol, signal, trade_amount)
        else:
            print("[ℹ️] No trade signal, waiting...")

        time.sleep(60)  # 1-minute interval, adjust as needed

if __name__ == "__main__":
    main()
