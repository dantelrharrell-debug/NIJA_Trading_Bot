import requests
import json

# Your live bot URL
WEBHOOK_URL = "https://nija-trading-bot-v9xl.onrender.com/webhook"

# Sample alert data to simulate a TradingView signal
sample_alert = {
    "pair": "BTCUSD",
    "allocation_percent": 10,
    "price": 50000,
    "time": "2025-10-02T12:00:00Z",
    "strategy": "buy"
}

try:
    response = requests.post(WEBHOOK_URL, json=sample_alert)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except json.JSONDecodeError:
        print("Response content:", response.text)
except Exception as e:
    print("Error sending test webhook:", e)
