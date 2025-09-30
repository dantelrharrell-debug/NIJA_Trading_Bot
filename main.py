from flask import Flask, request
import json
import os
import ccxt

app = Flask(__name__)

# Initialize Spot and Futures clients
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

@app.route("/", methods=["GET"])
def root():
    base_text = "Nija Trading Bot is live ✅"
    modes = detect_trading_status()

    # Helper to format last order nicely
    def format_order(order):
        if not order:
            return "No trades yet"
        # ccxt order/trade fields may vary by exchange
        side = order.get('side', 'N/A')
        symbol = order.get('symbol', 'N/A')
        amount = order.get('amount', order.get('size', 'N/A'))
        price = order.get('price', 'N/A')
        timestamp = order.get('timestamp')
        ts_str = "N/A"
        if timestamp:
            import datetime
            ts_str = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        return f"{symbol} | {side} | {amount} @ {price} | {ts_str}"

    # Build HTML
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
