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


# --- Example bot (simulated) ---
class Bot:
    def run_bot(self):
        while True:
            # Simulate trading every 10 seconds (for testing)
            time.sleep(10)
            with _lock:
                global trade_count
                trade_count += 1
                _trades.append({
                    "id": trade_count,
                    "timestamp": time.time(),
                    "iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "symbol": "BTC-USD",
                    "side": "BUY",
                    "amount": 0.01,
                    "price": 43000
                })


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


@app.route("/trades/recent", methods=["GET"])
def trades_recent():
    limit = int(request.args.get("limit", 5))
    with _lock:
        recent_trades = _trades[-limit:]
    return jsonify(recent_trades), 200


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

    return jsonify({"ok": True}), 200


# --- Main startup block ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Using PORT={port}")

    try:
        threading.Thread(target=bot.run_bot, daemon=True).start()
        print("[startup] Bot thread started")
    except Exception as e:
        print("[startup] Bot thread failed:", e)

    time.sleep(1)
    app.run(host="0.0.0.0", port=port)
