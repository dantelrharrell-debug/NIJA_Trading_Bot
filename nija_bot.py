import os
import time
import threading
from coinbase_advanced_py import CoinbaseAdvanced

# -------------------
# Initialize Coinbase client
# -------------------
client = CoinbaseAdvanced(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    api_pem_b64=os.getenv("API_PEM_B64")
)

# -------------------
# Strategy: Nija Signal (VWAP + RSI + Trend)
# -------------------
def nija_trade_signal():
    """
    Determines the best trade side (buy/sell) and dynamic size
    based on VWAP, RSI, EMA trend logic.
    Returns dict: {'side': 'buy'/'sell', 'size': float, 'trail_pct': float}
    """
    # Fetch BTC ticker & historical candles
    candles = client.get_historic_candles("BTC-USD", granularity=60, limit=50)
    prices = [float(c[4]) for c in candles]  # closing prices

    # Simple VWAP calculation
    vwap = sum(prices) / len(prices)
    current_price = prices[-1]

    # Simple RSI calculation (14-period)
    gains = [max(0, prices[i] - prices[i-1]) for i in range(1, len(prices))]
    losses = [max(0, prices[i-1] - prices[i]) for i in range(1, len(prices))]
    avg_gain = sum(gains[-14:])/14
    avg_loss = sum(losses[-14:])/14
    rsi = 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss != 0 else 100

    # EMA trend (20-period)
    ema = sum(prices[-20:])/20

    # Signal logic
    if current_price > vwap and rsi < 70 and current_price > ema:
        side = "buy"
    elif current_price < vwap and rsi > 30 and current_price < ema:
        side = "sell"
    else:
        return None  # no trade

    # Dynamic sizing (2% - 10% of account equity)
    account = client.get_account("USD")
    equity = float(account['balance'])
    size_pct = 0.05  # can adjust dynamically
    size = (equity * size_pct) / current_price

    return {"side": side, "size": round(size, 6), "trail_pct": 0.005}  # 0.5% trailing

# -------------------
# Execute trade
# -------------------
def execute_trade():
    trade = nija_trade_signal()
    if trade:
        order = client.place_order(
            symbol="BTC-USD",
            side=trade["side"],
            type="market",
            size=trade["size"],
            trailing_stop_pct=trade["trail_pct"]
        )
        print("🚀 LIVE TRADE EXECUTED:", order)
    else:
        print("⏸ No trade signal currently.")

# -------------------
# Trailing stop monitor (background)
# -------------------
def trailing_stop_monitor():
    while True:
        try:
            open_orders = client.get_open_orders("BTC-USD")
            ticker = client.get_ticker("BTC-USD")
            current_price = float(ticker['price'])
            for order in open_orders:
                side = order['side']
                stop_price = float(order.get('stop_price', 0))
                trail_pct = float(order.get('trailing_stop_pct', 0.005))

                if side == "buy":
                    new_stop = max(stop_price, current_price * (1 - trail_pct))
                    if new_stop > stop_price:
                        client.modify_order(order_id=order['id'], stop_price=new_stop)
                        print(f"⬆ BUY trailing stop updated: {new_stop:.2f}")
                elif side == "sell":
                    new_stop = min(stop_price, current_price * (1 + trail_pct))
                    if new_stop < stop_price or stop_price == 0:
                        client.modify_order(order_id=order['id'], stop_price=new_stop)
                        print(f"⬇ SELL trailing stop updated: {new_stop:.2f}")

        except Exception as e:
            print("⚠ Trailing stop error:", e)
        time.sleep(5)

# -------------------
# Start background monitor
# -------------------
monitor_thread = threading.Thread(target=trailing_stop_monitor, daemon=True)
monitor_thread.start()
print("🚀 Trailing stop monitor running in background.")

# -------------------
# Main loop (every minute)
# -------------------
while True:
    execute_trade()
    time.sleep(60)  # check every 1 minute
