import os
import threading
from flask import Flask, jsonify
from nija import NijaBot

# Initialize Flask app
app = Flask(__name__)

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

# Function to start trading in a background thread
def start_trading():
    nija.run_live()  # Actual method to start trading continuously

trading_thread = threading.Thread(target=start_trading, daemon=True)
trading_thread.start()

# Basic root route to confirm the bot is live
@app.route("/", methods=["GET"])
def root():
    return "Nija Trading Bot is live and trading ✅", 200

# Endpoint to get a summary of trades
@app.route("/trades", methods=["GET"])
def trades_summary():
    # Replace with your bot's actual methods for trade data
    with nija.lock:  # Only if your bot uses a lock for thread safety
        total = nija.get_total_trades()
        last_trade = nija.get_last_trade()
        recent_1h = nija.get_trades_last_hour()
        recent_24h = nija.get_trades_last_24h()

    return jsonify({
        "total_trades": total,
        "recent": {
            "last_1_hour": recent_1h,
            "last_24_hours": recent_24h
        },
        "last_trade": last_trade
    })

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
