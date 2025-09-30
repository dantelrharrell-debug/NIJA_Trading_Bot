from flask import Flask, jsonify, render_template_string
import os
import datetime

app = Flask(__name__)

def detect_trading_status():
    # Simple dummy data to test deployment
    return {
        "spot": True,
        "perpetual": True,
        "active_spot_trades": False,
        "active_perp_trades": False,
        "last_spot_order": {
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.001,
            "price": 27000,
            "timestamp": datetime.datetime.now().timestamp() * 1000
        },
        "last_perp_order": {
            "symbol": "ETH/USDT",
            "side": "sell",
            "amount": 0.01,
            "price": 1800,
            "timestamp": datetime.datetime.now().timestamp() * 1000
        },
        "details": ["Dummy deploy — no API calls yet"]
    }

def format_order(order):
    if not order:
        return "No trades yet"
    ts_str = datetime.datetime.fromtimestamp(order["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return f"{order['symbol']} | {order['side']} | {order['amount']} @ {order['price']} | {ts_str}"

@app.route("/")
def root():
    modes = detect_trading_status()
    html = f"""
    <html>
    <head><title>Nija Bot</title></head>
    <body style="font-family: Arial; text-align:center; padding:30px;">
        <h1>Nija Bot is live ✅</h1>
        <div>
            <div style="margin:8px; padding:12px; border:1px solid #ddd; display:inline-block;">
                <strong>Spot</strong><br>
                Configured: {modes['spot']}<br>
                Active Trades: {modes['active_spot_trades']}<br>
                Last Trade: <br>{format_order(modes['last_spot_order'])}
            </div>
            <div style="margin:8px; padding:12px; border:1px solid #ddd; display:inline-block;">
                <strong>Perpetual</strong><br>
                Configured: {modes['perpetual']}<br>
                Active Trades: {modes['active_perp_trades']}<br>
                Last Trade: <br>{format_order(modes['last_perp_order'])}
            </div>
        </div>
        <p>JSON status: <a href="/status">/status</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/status")
def status():
    return jsonify(detect_trading_status())

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
