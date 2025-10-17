#!/usr/bin/env python3
import os
import json
import requests
from coinbase_advanced_py import CoinbaseClient

# -----------------------------
# Load environment variables
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")
PASSPHRASE = os.getenv("PASSPHRASE")
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# Always disable mock if live trading
USE_MOCK = not LIVE_TRADING
SANDBOX = USE_MOCK

# -----------------------------
# Initialize Coinbase client
# -----------------------------
try:
    client = CoinbaseClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        passphrase=PASSPHRASE,
        pem_b64=API_PEM_B64,
        sandbox=SANDBOX
    )
    print(f"✅ Coinbase client initialized. Sandbox={SANDBOX}, Live={LIVE_TRADING}")
except Exception as e:
    print("❌ Coinbase client failed to initialize:", e)
    exit(1)

# -----------------------------
# Print account balances
# -----------------------------
try:
    accounts = client.get_accounts()
    print("💰 Your Coinbase balances:")
    for acc in accounts:
        print(f"{acc['currency']}: {acc['balance']}")
except Exception as e:
    print("⚠️ Could not fetch accounts:", e)

# -----------------------------
# Test a mock webhook signal
# -----------------------------
try:
    test_signal = {
        "secret": TV_WEBHOOK_SECRET,
        "signal": "buy",
        "pair": "BTC-USD",
        "amount": 0.0001
    }

    # Replace <your-railway-url> with your project URL
    webhook_url = f"https://<your-railway-project>.up.railway.app/webhook"

    resp = requests.post(webhook_url, json=test_signal)
    print(f"🔔 Webhook test sent: Status {resp.status_code}, Response: {resp.text}")

except Exception as e:
    print("❌ Failed to send test webhook:", e)
