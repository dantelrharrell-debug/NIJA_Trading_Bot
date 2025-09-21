# app.py (snippet)
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken")
LIVE = os.getenv("NIJA_LIVE", "false").lower() == "true"

@app.get("/health")
def health():
    return jsonify({"status":"ok","live":LIVE})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

main.py
Procfile
requirements.txt


app = Flask(__name__)

# --- Coinbase client ---
client = cbpro.AuthenticatedClient(
    os.getenv("COINBASE_API_KEY"),
    os.getenv("COINBASE_API_SECRET"),
    os.getenv("COINBASE_API_PASSPHRASE")
)

# --- Webhook secret ---
WEBHOOK_SECRET = os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken")

# --- Health check route ---
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# --- Webhook route ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    token = data.get("token")

    # Security check
    if token != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Extract trading info
    symbol = data.get("symbol")
    action = data.get("action").lower()  # "buy" or "sell"
    price = float(data.get("price"))
    quantity = float(data.get("quantity"))

    # Convert TradingView symbol to Coinbase format if needed
    coinbase_symbol = symbol.replace("/", "-")

    # Execute trade
    try:
        order = client.place_market_order(
            product_id=coinbase_symbol,
            side=action,
            funds=None,
            size=quantity
        )
        print(f"Executed {action.upper()} {quantity} {coinbase_symbol} at market")
        return jsonify({"status": "success", "order": order}), 200
    except Exception as e:
        print("Trade error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Root route ---
@app.route("/", methods=["GET"])
def home():
    return "NIJA Bot is running! 🚀"

# --- Start server and ngrok tunnel ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    public_url = ngrok.connect(port)
    print(f"🔗 Public URL: {public_url}")
    app.run(host="0.0.0.0", port=port)

port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)

symbol = data.get("symbol")
action = data.get("action").lower()
quantity = float(data.get("quantity"))
coinbase_symbol = symbol.replace("/", "-")
order = client.place_market_order(product_id=coinbase_symbol, side=action, size=quantity)

# ---- Paste at the bottom of main.py if using Flask ----
if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    # if your Flask app variable is not 'app', replace 'app' below with your variable name
    try:
        app.run(host="0.0.0.0", port=port)
    except NameError:
        # fallback if main.py is not a Flask app
        print("Started main.py (not a Flask 'app').")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
