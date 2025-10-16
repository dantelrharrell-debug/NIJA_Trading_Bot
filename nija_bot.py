#!/usr/bin/env python3
import os
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --------------------------
# Flask App
# --------------------------
app = Flask(__name__)

# --------------------------
# Config
# --------------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

# --------------------------
# Routes
# --------------------------
@app.route("/")
def home():
    """
    Simple health check endpoint.
    """
    return jsonify({
        "status": "OK",
        "mock_mode": USE_MOCK
    })

@app.route("/accounts")
def accounts():
    """
    Returns Coinbase account balances if live mode.
    In mock mode, returns dummy data.
    """
    if USE_MOCK:
        return jsonify({
            "mock": True,
            "accounts": [
                {"currency": "BTC", "available": "0.5"},
                {"currency": "USD", "available": "1000"}
            ]
        })

    # Live mode
    try:
        import coinbase_advanced_py as cb

        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PEM_B64 = os.getenv("API_PEM_B64")

        client = cb.CoinbaseAdvanced(
            key=API_KEY,
            secret=API_SECRET,
            pem_b64=API_PEM_B64,
            sandbox=False  # False for live trading
        )

        accounts_data = client.get_accounts()
        accounts_list = [
            {"currency": acc["currency"], "available": acc["available"]}
            for acc in accounts_data
        ]

        return jsonify({
            "mock": False,
            "accounts": accounts_list
        })

    except Exception as e:
        return jsonify({"error": "Coinbase connection failed", "details": str(e)}), 500

# --------------------------
# Main check (optional for local run)
# --------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
