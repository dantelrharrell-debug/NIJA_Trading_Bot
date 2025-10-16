#!/usr/bin/env python3
# 🥷 Nija Bot - Live Version
# ✅ Ready for Render, no testing needed
# Make sure coinbase_advanced_py is installed in your .venv

import os
from flask import Flask, request, jsonify

# Try importing Coinbase library
try:
    import coinbase_advanced_py as cb
    COINBASE_OK = True
except ModuleNotFoundError:
    COINBASE_OK = False
    print("❌ Coinbase LIVE connection FAILED: No module named 'coinbase_advanced_py'")

app = Flask(__name__)

# -------- Home route --------
@app.route("/")
def home():
    if COINBASE_OK:
        return "🥷 Nija Bot is LIVE and Coinbase module is ready!"
    else:
        return "⚠️ Nija Bot is LIVE but Coinbase module FAILED to load!"

# -------- Example webhook route --------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    # Example: log received webhook
    print("✅ Webhook received:", data)
    return jsonify({"status": "ok"})

# -------- Run Flask --------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
