from flask import Flask, jsonify, request
import threading
import time
import os

app = Flask(__name__)

# --- Simulated trading data ---
_trades = []
trade_count = 0
_lock = threading.Lock()


# --- Helper function to count trades in a time window ---
def _count_in_window(seconds):
    now = time.time()
    with _lock:
        return sum(1 for t in _trades if now - t["timestamp"] <= seconds)


# --- Bot (simulated) ---
class Bot:
    def run_bot(self):
        while True:
            time.sleep(10)  # simulate a trade every 10 seconds
            with _lock:
                global trade_count
                trade_count += 1
                trade = {
                    "id": trade_count,
                    "timestamp": time.time(),
                    "iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "symbol": "BTC-USD",
                    "side": "BUY",
                    "amount": 0.01,
                    "price": 43000
                }
                _trades.append(trade)
                print(f"[BOT] New trade added: {trade}")


bot = Bot()


# --- Flask routes ---

@app.route("/trades", methods=["GET"])
def trades_summary():
    with _lock:
        total = trade_count
        last = _trades[-1] if len(_trades) > 0 else None

    last_hour = _count_in_window(3600)
    last_24h = _count_in_window(3600 * 24)

    resp = {
        "total_trades": total,
        "recent": {
            "last_1_hour": last_hour,
            "last_24_hours": last_24h
        },
        "last_trade": last
    }

    return jsonify(resp), 200


@app.route("/trades/test_add", methods=["POST"])
def trades_test_add():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    with _lock:
        global trade_count
        trade_count += 1
        trade = {
            "id": trade_count,
            "timestamp": time.time(),
            "iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "symbol": data.get("symbol", "TEST-USD"),
            "side": data.get("side", "BUY"),
            "amount": data.get("amount", 0.01),
            "price": data.get("price", 100)
        }
        _trades.append(trade)
        print(f"[TEST ADD] Trade added: {trade}")

    return jsonify({"ok": True}), 200


# --- Main startup ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Using PORT={port}")

    # start bot in background thread
    try:
        threading.Thread(target=bot.run_bot, daemon=True).start()
        print("[startup] Bot thread started")
    except Exception as e:
        print("[startup] Bot thread failed:", e)

    print("[startup] Flask server starting...")

    # run Flask in same tab, logs will show in Shell
    app.run(host="0.0.0.0", port=port)
