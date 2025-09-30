# main.py
import os
import ccxt
import json
import traceback
from flask import Flask, request
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

# Coinbase keys
COINBASE_SPOT_KEY = os.getenv('COINBASE_SPOT_KEY')
COINBASE_SPOT_SECRET = os.getenv('COINBASE_SPOT_SECRET')
COINBASE_SPOT_PASSPHRASE = os.getenv('COINBASE_SPOT_PASSPHRASE')

COINBASE_FUTURES_KEY = os.getenv('COINBASE_FUTURES_KEY')
COINBASE_FUTURES_SECRET = os.getenv('COINBASE_FUTURES_SECRET')
COINBASE_FUTURES_PASSPHRASE = os.getenv('COINBASE_FUTURES_PASSPHRASE')

# ---------------------------
# Initialize Coinbase clients
# ---------------------------
try:
    spot_client = ccxt.coinbase({
        'apiKey': COINBASE_SPOT_KEY,
        'secret': COINBASE_SPOT_SECRET,
        'password': COINBASE_SPOT_PASSPHRASE,
        'enableRateLimit': True,
    })
    futures_client = ccxt.coinbase({
        'apiKey': COINBASE_FUTURES_KEY,
        'secret': COINBASE_FUTURES_SECRET,
        'password': COINBASE_FUTURES_PASSPHRASE,
        'enableRateLimit': True,
    })

    # Test connections
    spot_markets = spot_client.fetch_markets()
    futures_markets = futures_client.fetch_markets()
    print(f"✅ Spot Auth Success! Markets: {len(spot_markets)}")
    print(f"✅ Futures Auth Success! Markets: {len(futures_markets)}")
except Exception as e:
    print("❌ Coinbase auth failed:", type(e).__name__, str(e))
    traceback.print_exc()
    exit(1)

# ---------------------------
# Initialize Flask app
# ---------------------------
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.data.decode("utf-8")
    print("INFO: Raw body received:", raw_body)

    # Try to parse JSON
    parsed = None
    try:
        parsed = json.loads(raw_body)
        print("✅ Parsed JSON:", parsed)
    except json.JSONDecodeError:
        print("⚠️ Webhook body is not JSON, processing as plain text")
        parsed = {"raw_text": raw_body}

    # Determine trade type and execute
    side = parsed.get("side")
    symbol = parsed.get("symbol")
    market_type = parsed.get("market_type", "spot")  # default to spot

    if side and symbol:
        if market_type.lower() == "futures":
            client = futures_client
        else:
            client = spot_client

        print(f"Trading signal: {side.upper()} {symbol} on {market_type.upper()}")
        # TODO: Add your trade execution logic:
        # client.create_order(symbol, 'market', side, amount)
    else:
        print(f"Received plain text alert: {parsed['raw_text']}")

    return "OK", 200

# ---------------------------
# Start Nija Trading Bot
# ---------------------------
print("🚀 Starting Nija Trading Bot...")

# ---------------------------
# Run Flask server
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
