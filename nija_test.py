import requests
import os

# Replace with your Render app's live URL
BASE_URL = os.getenv("NIJA_BOT_URL", "https://nija-trading-bot-v9xl.onrender.com")

def check_status():
    try:
        r = requests.get(f"{BASE_URL}/status", timeout=5)
        if r.status_code == 200:
            print("[STATUS] Coinbase client connected:", r.json())
        else:
            print("[STATUS] Error:", r.status_code, r.text)
    except Exception as e:
        print("[STATUS] Could not reach /status:", e)

def test_webhook():
    payload = {
        "symbol": "BTC-USD",
        "action": "buy",
        "size": 0.001
    }
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=payload, timeout=5)
        print("[WEBHOOK] Response:", r.status_code, r.json())
    except Exception as e:
        print("[WEBHOOK] Could not reach /webhook:", e)

if __name__ == "__main__":
    print("== Checking Nija Bot ==")
    check_status()
    test_webhook()
    print("== Test Complete ==")
