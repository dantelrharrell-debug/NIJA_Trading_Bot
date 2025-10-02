import requests, json

WEBHOOK_URL = "https://nija-trading-bot-v9xl.onrender.com/webhook"

tests = [
    # strict Order schema (should be accepted)
    {
        "name": "Strict Order",
        "json": {
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "market",
            "amount": 0.01
        }
    },
    # legacy TradingView style (should be accepted by legacy branch)
    {
        "name": "Legacy TV Alert",
        "json": {
            "pair": "BTCUSD",
            "allocation_percent": 10,
            "price": 50000,
            "time": "2025-10-02T12:00:00Z",
            "strategy": "buy"
        }
    },
    # intentionally invalid (to see error response)
    {
        "name": "Invalid payload",
        "json": {
            "foo": "bar"
        }
    }
]

for t in tests:
    print("=== TEST:", t["name"], "===")
    try:
        r = requests.post(WEBHOOK_URL, json=t["json"], timeout=10)
        print("Status:", r.status_code)
        # try pretty print JSON if possible
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print("Text:", r.text)
    except Exception as e:
        print("Request failed:", e)
    print()
