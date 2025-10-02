import requests, json

WEBHOOK_URL = "https://nija-trading-bot-v9xl.onrender.com/webhook"

sample_order = {"symbol":"BTC-USD","side":"buy","order_type":"market","amount":0.01}

r = requests.post(WEBHOOK_URL, json=sample_order, timeout=10)
print("Status:", r.status_code)
try:
    print(json.dumps(r.json(), indent=2))
except Exception:
    print(r.text)
