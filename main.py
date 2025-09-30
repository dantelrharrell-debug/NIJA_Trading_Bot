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

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.data.decode("utf-8")
    print("INFO: Raw body received:", raw_body)

    # Try to parse JSON
    try:
        alert = json.loads(raw_body)
        print("✅ Parsed JSON:", alert)
    except json.JSONDecodeError:
        print("⚠️ Webhook body is not JSON, processing as plain text")
        alert = {"raw_text": raw_body}

    # Determine which client to use
    client = None
    market_type = "unknown"

    # Example JSON alert: {"symbol": "BTC/USD", "side": "buy", "amount": "0.001", "market": "spot"}
    if "market" in alert:
        if alert["market"].lower() == "spot":
            client = SPOT_CLIENT
            market_type = "Spot"
        elif alert["market"].lower() == "futures":
            client = FUTURES_CLIENT
            market_type = "Futures"

    # Place a test order if valid
    if client and "symbol" in alert and "side" in alert and "amount" in alert:
        symbol = alert["symbol"]
        side = alert["side"]
        amount = float(alert["amount"])
        try:
            print(f"🔔 Placing {side.upper()} order for {amount} {symbol} on {market_type}")
            order = client.create_order(symbol, 'market', side, amount)
            print("✅ Order placed:", order)
        except Exception as e:
            print(f"❌ Order failed:", type(e).__name__, e)
    else:
        print(f"⚠️ Ignored webhook: {alert}")

    return "OK", 200

if __name__ == "__main__":
    print("🚀 Nija Trading Bot Webhook running on port 8080")
    app.run(host="0.0.0.0", port=8080)
