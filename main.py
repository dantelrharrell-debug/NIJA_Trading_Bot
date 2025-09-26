# main.py

import threading
import time
from flask import Flask, jsonify
from nija import NijaBot  # Make sure this matches your bot class in nija.py

# === Initialize your trading bot ===
nija = NijaBot()  # adjust arguments if your bot needs any

# === Start the bot in a background thread ===
def run_bot():
    try:
        nija.start_trading()  # replace with your bot’s actual start method
    except Exception as e:
        print("Error starting bot:", e)

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True  # ensures thread exits when main program exits
bot_thread.start()

# === Flask app for Render/Gunicorn ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Nija Trading Bot is live ✅"

@app.route("/status")
def status():
    """Return bot status"""
    return jsonify({
        "trading": getattr(nija, "is_trading", False),  # True/False if bot running
        "total_trades": getattr(nija, "total_trades", 0)
    })

@app.route("/trades")
def trades_summary():
    """Return recent trades"""
    recent = getattr(nija, "get_recent_trades", lambda: [])()
    return jsonify({
        "total_trades": getattr(nija, "total_trades", 0),
        "recent": recent,
        "last_trade": recent[-1] if recent else None
    })

# === Keep app running locally if needed ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
