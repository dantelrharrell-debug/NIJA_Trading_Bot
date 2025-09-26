import os
import json
import threading
from flask import Flask, jsonify
from nija import NijaBot
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Path for trade logs
TRADE_LOG_FILE = "trade_log.json"

# Ensure trade log file exists
if not os.path.exists(TRADE_LOG_FILE):
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump([], f)

# Initialize NijaBot using environment variables
nija = NijaBot(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    live=os.getenv("LIVE", "False").lower() == "true",
    tp_percent=float(os.getenv("TP_PERCENT", 1.0)),
    sl_percent=float(os.getenv("SL_PERCENT", 1.0)),
    trailing_stop=float(os.getenv("TRAILING_STOP", 0.5)),
    trailing_tp=float(os.getenv("TRAILING_TP", 0.5)),
    smart_logic=os.getenv("SMART_LOGIC", "True").lower() == "true"
)

# Function to log a trade to JSON
def log_trade(trade):
    trade_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **trade
    }
    # Read existing logs
    with threading.Lock():
        with open(TRADE_LOG_FILE, "r+") as f:
            data = json.load(f)
            data.append(trade_entry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

# Wrapper to capture trades and log them
def start_trading():
    for trade in nija.run_live():  # Assuming run_live() yields each trade
        log_trade(trade)

# Start trading in a background thread
trading_thread = threading.Thread(target=start_trading, daemon=True)
trading_thread.start()

# Basic root route
@app.route("/", methods=["GET"])
def root():
    return "Nija Trading Bot is live and trading ✅", 200

# Endpoint to get a summary of trades
@app.route("/trades", methods=["GET"])
def trades_summary():
    with threading.Lock():
        with open(TRADE_LOG_FILE, "r") as f:
            data = json.load(f)

    last_trade = data[-1] if data else None
    recent_1h = sum(1 for t in data if (datetime.utcnow() - datetime.fromisoformat(t["timestamp"])).total_seconds() <= 3600)
    recent_24h = sum(1 for t in data if (datetime.utcnow() - datetime.fromisoformat(t["timestamp"])).total_seconds() <= 86400)

    return jsonify({
        "total_trades": len(data),
        "recent": {
            "last_1_hour": recent_1h,
            "last_24_hours": recent_24h
        },
        "last_trade": last_trade
    })

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
