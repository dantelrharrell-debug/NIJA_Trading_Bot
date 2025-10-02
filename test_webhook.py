import requests
import json

# Replace this with your live bot URL
WEBHOOK_URL = "https://nija-bot.onrender.com/webhook"

# Sample alert data
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
    print("Response:", response.json())
except Exception as e:
    print("Error sending test webhook:", e)
