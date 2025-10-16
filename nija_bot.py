#!/usr/bin/env python3
import os
import traceback

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully.")
except ModuleNotFoundError:
    print("❌ Coinbase LIVE connection FAILED: No module named 'coinbase_advanced_py'")

from flask import Flask, request, jsonify

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    # Your webhook logic here
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
