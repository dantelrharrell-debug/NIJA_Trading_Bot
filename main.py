import os
import json
from flask import Flask, request, render_template_string
import ccxt

# Coinbase clients via env vars
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

# Test connections (will print 401 if keys missing/invalid)
try:
    print("Spot balance:", SPOT_CLIENT.fetch_balance())
except Exception as e:
    print("Error connecting to Spot:", e)

try:
    print("Futures balance:", FUTURES_CLIENT.fetch_balance())
except Exception as e:
    print("Error connecting to Futures:", e)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = json.loads(request.data)
        print("Received alert:", data)

        market = data.get("market", "spot").lower()
        symbol = data.get("symbol")
        side = data.get("side")
        amount = float(data.get("amount", 0))

        if not symbol or side not in ['buy', 'sell'] or amount <= 0:
            return "Invalid order data", 400

        client = SPOT_CLIENT if market == "spot" else FUTURES_CLIENT
        client.load_markets()
        min_size = float(client.markets[symbol]['limits']['amount']['min'])
        if amount < min_size:
            print(f"Adjusting amount {amount} -> min {min_size}")
            amount = min_size

        order = client.create_order(symbol=symbol, type='market', side=side, amount=amount)
        print("Order submitted:", order)
        return "Order executed", 200

    except Exception as e:
        print("Error processing webhook:", e)
        return f"Error: {str(e)}", 500

@app.route("/", methods=["GET"])
def root():
    return "<h2>Nija Trading Bot is live (Spot + Futures)</h2>", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


