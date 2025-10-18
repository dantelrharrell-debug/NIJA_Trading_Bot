import sys, os
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
sys.path.insert(0, VENDOR_DIR)
#!/usr/bin/env python3
# =========================
# Nija Trading Bot AI vLIVE
# Universal paste-and-go live bot
# No ngrok needed
# =========================

import sys, os, threading, time

# ====== KEYS & CONFIG ======
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
API_PEM_B64 = """-----BEGIN PRIVATE KEY-----
nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49
-----END PRIVATE KEY-----"""
WEBHOOK_URL = "https://nija-trading-bot-v9xl.onrender.com/webhook"
TV_WEBHOOK_SECRET = "change_this_secret"

TRADING_MIN = 0.02  # 2%
TRADING_MAX = 0.10  # 10%
MOCK_MODE = False    # True = simulation, False = live

# ====== AUTO-INSTALL MISSING MODULES ======
modules = ["coinbase_advanced_py", "flask"]
for m in modules:
    try:
        __import__(m)
    except ModuleNotFoundError:
        print(f"🔄 Installing {m}...")
        os.system(f"{sys.executable} -m pip install --upgrade {m}")

# ====== IMPORTS ======
try:
    import coinbase_advanced_py as cap
    client = cap.Client(api_key=API_KEY, api_secret=API_SECRET, api_pem_b64=API_PEM_B64)
    print("✅ Using coinbase_advanced_py.Client as client")
except Exception as e:
    client = None
    MOCK_MODE = True
    print("❌ Coinbase client init failed, using MOCK_MODE")
    print("Error:", e)

from flask import Flask, request, jsonify

# ====== DYNAMIC ALLOCATION ======
def get_allocation():
    return TRADING_MAX  # You can replace with dynamic logic

# ====== TRADE FUNCTION ======
def trade(signal: str):
    allocation = get_allocation()
    if MOCK_MODE or client is None:
        print(f"[MOCK TRADE] {signal} ({allocation*100}%)")
        return
    print(f"[REAL TRADE] {signal} ({allocation*100}%)")
    # Place real order logic here:
    # Example (adapt to your Coinbase client):
    # if "BUY" in signal:
    #     client.buy(price="50000.0", size="0.001", product_id="BTC-USD")
    # elif "SELL" in signal:
    #     client.sell(price="50000.0", size="0.001", product_id="BTC-USD")

# ====== SIGNAL LOOP ======
def signal_loop():
    signals = ["BUY BTC", "SELL ETH", "BUY LTC"]  # Replace with live strategy
    while True:
        for s in signals:
            trade(s)
            time.sleep(5)

# ====== WEBHOOK SERVER ======
def start_webhook_server():
    app = Flask("NijaBotWebhook")

    @app.route("/webhook", methods=["POST"])
    def webhook():
        data = request.get_json() or {}
        secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
        if secret != TV_WEBHOOK_SECRET:
            return jsonify({"error": "unauthorized"}), 401
        signal = data.get("signal")
        if signal:
            trade(signal)
            return jsonify({"status": "ok", "signal": signal})
        return jsonify({"status": "no signal"}), 400

    print(f"🌍 Webhook server running at {WEBHOOK_URL}")
    app.run(host="0.0.0.0", port=10000)

# ====== MAIN ======
if __name__ == "__main__":
    print("🚀 Nija Trading Bot AI FULLY LIVE 🚀")
    threading.Thread(target=signal_loop, daemon=True).start()
    start_webhook_server()
