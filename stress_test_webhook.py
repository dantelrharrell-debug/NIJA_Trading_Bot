import requests
import json
import time
import random

# Replace with your live bot URL
WEBHOOK_URL = "https://<your-render-url>.onrender.com/webhook"

# Sample trading pairs
pairs = ["BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD"]

# Number of test alerts to send
NUM_ALERTS = 20

for i in range(NUM_ALERTS):
    pair = random.choice(pairs)
    action = random.choice(["buy", "sell"])
    allocation_percent = random.choice([5, 10, 15, 20])
    price = round(random.uniform(100, 60000), 2)
    alert = {
        "pair": pair,
        "allocation_percent": allocation_percent,
        "price": price,
        "time": "2025-10-02T12:00:00Z",
        "strategy": action
    }

    try:
        response = requests.post(WEBHOOK_URL, json=alert)
        print(f"{i+1}/{NUM_ALERTS} | Sent {action.upper()} for {pair} with {allocation_percent}% allocation")
        print("Response:", response.json())
    except Exception as e:
        print(f"Error sending alert {i+1}:", e)

    time.sleep(1)  # Optional delay to avoid overwhelming the server
