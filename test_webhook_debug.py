import requests
import json
import time

# Replace with your live bot URL
WEBHOOK_URL = "https://<your-render-url>.onrender.com/webhook"

# Sample alert data
sample_alert = {
    "pair": "BTCUSD",
    "allocation_percent": 10,
    "price": 50000,
    "time": "2025-10-02T12:00:00Z",
    "strategy": "buy"
}

def send_webhook(alert):
    try:
        response = requests.post(WEBHOOK_URL, json=alert, timeout=10)
        print("Webhook sent successfully!")
        print("Status Code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Response Text:", response.text)
    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        print("Retrying in 2 seconds...")
        time.sleep(2)
        try:
            response = requests.post(WEBHOOK_URL, json=alert, timeout=10)
            print("Retry successful!")
            print("Status Code:", response.status_code)
            try:
                print("Response JSON:", response.json())
            except Exception:
                print("Response Text:", response.text)
        except Exception as e2:
            print("Retry failed:", e2)

if __name__ == "__main__":
    send_webhook(sample_alert)
