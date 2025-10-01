# ================================
# 1️⃣ Imports
# ================================
import os
import json
from flask import Flask, request, render_template_string
import ccxt
import datetime

# ================================
# 2️⃣ Initialize Flask
# ================================
app = Flask(__name__)

# ================================
# 3️⃣ Coinbase Advanced API setup (env variables)
# ================================
SPOT_CLIENT = ccxt.coinbase({
    'apiKey': os.getenv("COINBASE_SPOT_KEY"),
    'secret': os.getenv("COINBASE_SPOT_SECRET"),
    'password': os.getenv("COINBASE_SPOT_PASSPHRASE"),
    'enableRateLimit': True,
})

FUTURES_CLIENT = ccxt.coinbase({
    'apiKey': os.getenv("COINBASE_FUTURES_KEY"),
    'secret': os.getenv("COINBASE_FUTURES_SECRET"),
    'password': os.getenv("COINBASE_FUTURES_PASSPHRASE"),
    'enableRateLimit': True,
})

# Test connection
try:
    balance = SPOT_CLIENT.fetch_balance()
    print("Coinbase connection successful! Balance:", balance)
except Exception as e:
    print("Error connecting to Coinbase:", e)

# ================================
# 4️⃣ Helper functions
# ================================
def format_order(order):
    if not order:
        return "No trades yet"
    side = order.get('side', 'N/A')
    symbol = order.get('symbol', 'N/A')
    amount = order.get('amount', order.get('size', 'N/A'))
    price = order.get('price', 'N/A')
    timestamp = order.get('timestamp')
    ts_str = "N/A"
    if timestamp:
        ts_str = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return f"{symbol} | {side} | {amount} @ {price} | {ts_str}"

def detect_trading_status():
    # Placeholder logic for demo
    return {
        'spot': 'configured',
        'perpetual': 'configured',
        'active_spot_trades': 0,
        'active_perp_trades': 0,
        'last_spot_order': None,
        'last_perp_order': None
    }

# ================================
# 5️⃣ Webhook for TradingView alerts (with min order check)
# ================================
@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    print("Received alert:", data)

    symbol = 'BTC-USD'

    # Load market info to get minimum size
    SPOT_CLIENT.load_markets()
    min_size = float(SPOT_CLIENT.markets[symbol]['limits']['amount']['min'])
    print(f"Minimum order size for {symbol}: {min_size}")

    # Intended order amount
    order_amount = 0.001  # adjust according to signal

    # Ensure order meets minimum
    if order_amount < min_size:
        print(f"Order amount {order_amount} is below minimum {min_size}. Adjusting to minimum.")
        order_amount = min_size

    # Place market buy order
    try:
        order = SPOT_CLIENT.create_order(
            symbol=symbol,
            type='market',
            side='buy',
            amount=order_amount
        )
        print("Order submitted:", order)
    except Exception as e:
        print("Error submitting order:", e)

    return "Webhook received", 200

# ================================
# 6️⃣ Status page
# ================================
@app.route("/", methods=["GET"])
def root():
    base_text = "Nija Trading Bot is live ✅"
    modes = detect_trading_status()

    html = f"""
    <html>
      <head><title>Nija Trading Bot</title></head>
      <body style="font-family: Arial; text-align:center; padding:30px;">
        <h1>{base_text}</h1>
        <div style="margin-top:18px;">
          <div style="display:inline-block; margin:8px; padding:12px; border-radius:8px; border:1px solid #ddd;">
            <strong>Spot</strong><br>
            Configured: {modes['spot']}<br>
            Active Trades: {modes['active_spot_trades']}<br>
            Last Trade: <br><span style="font-size:12px; color:#333;">{format_order(modes['last_spot_order'])}</span>
          </div>
          <div style="display:inline-block; margin:8px; padding:12px; border-radius:8px; border:1px solid #ddd;">
            <strong>Perpetual</strong><br>
            Configured: {modes['perpetual']}<br>
            Active Trades: {modes['active_perp_trades']}<br>
            Last Trade: <br><span style="font-size:12px; color:#333;">{format_order(modes['last_perp_order'])}</span>
          </div>
        </div>
        <p style="font-size:12px; color:#666;">JSON status: <a href="/status">/status</a></p>
      </body>
    </html>
    """
    return render_template_string(html), 200

# ================================
# 7️⃣ Start Flask server
# ================================
if __name__ == '__main__':
    app.run(port=5000)
    if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)

