# main.py
import os
import ccxt
import traceback
from flask import Flask, request
from subprocess import Popen
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()  # loads .env

COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
COINBASE_API_SECRET = os.getenv('COINBASE_API_SECRET')
COINBASE_PASSPHRASE = os.getenv('COINBASE_PASSPHRASE')

# ---------------------------
# Initialize Coinbase client
# ---------------------------
try:
    coinbase_client = ccxt.coinbase({
        'apiKey': COINBASE_API_KEY,
        'secret': COINBASE_API_SECRET,
        'password': COINBASE_PASSPHRASE,
        'enableRateLimit': True,
    })
    markets = coinbase_client.fetch_markets()
    print(f"✅ Coinbase Auth Success! Fetched {len(markets)} markets")
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

    # Example: handle both JSON and plain text
    if "symbol" in parsed and "side" in parsed:
        print(f"Trading signal: {parsed['side']} {parsed['symbol']}")
        # TODO: Add your Nija bot trade execution logic here
    else:
        print(f"Received plain text alert: {parsed['raw_text']}")

    return "OK", 200

# ---------------------------
# Start Nija Trading Bot
# ---------------------------
print("🚀 Starting Nija Trading Bot...")

# Optional: run additional bot script in background
# Popen(["python", "nija_bot.py"])  # uncomment if needed

# ---------------------------
# Run Flask server
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
