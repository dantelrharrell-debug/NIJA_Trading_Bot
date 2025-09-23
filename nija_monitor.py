import requests
import os
import time
from datetime import datetime

# Replace with your Render service URL, or set via environment variable
BASE_URL = os.getenv("NIJA_BOT_URL", "https://your-nija-bot.onrender.com")
CHECK_INTERVAL = 15  # seconds between checks

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def check_status():
    try:
        resp = requests.get(f"{BASE_URL}/status", timeout=10)
        data = resp.json()
        if resp.status_code == 200 and data.get("status") == "connected":
            return True, "Coinbase client connected."
        else:
            return False, f"Status error: {resp.status_code} {data}"
    except Exception as e:
        return False, f"Status check failed: {e}"

def check_webhook():
    try:
        test_payload = {
            "symbol": "BTC-USD",
            "action": "buy",
            "size": "0.0001"  # small safe test size
        }
        resp = requests.post(f"{BASE_URL}/webhook", json=test_payload, timeout=10)
        data = resp.json()
        if resp.status_code == 200 and data.get("status") in ("success", "ignored"):
            return True, f"Webhook OK: {data.get('status')}"
        else:
            return False, f"Webhook error: {resp.status_code} {data}"
    except Exception as e:
        return False, f"Webhook check failed: {e}"

if __name__ == "__main__":
    log("Starting Nija bot health monitor...")
    while True:
        status_ok, status_msg = check_status()
        webhook_ok, webhook_msg = check_webhook()

        if status_ok and webhook_ok:
            log(f"✅ Bot healthy: {status_msg} | {webhook_msg}")
        else:
            log(f"⚠️ Bot issue detected!")
            if not status_ok:
                log(f"    {status_msg}")
            if not webhook_ok:
                log(f"    {webhook_msg}")

        time.sleep(CHECK_INTERVAL)
