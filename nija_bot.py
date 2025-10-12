import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from coinbase_advanced_py import Client  # This works once requirements.txt is correct

# Config
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", "8080"))

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

# Initialize Coinbase client
client = Client(API_KEY, API_SECRET)

# Quick balance check
try:
    balances = client.get_account_balances()
    print("✅ Nija connected! Balances:", balances)
except Exception as e:
    print("⚠️ Connection failed:", e)

# Bot loop
def bot_loop():
    while True:
        try:
            accounts = client.get_account_balances()
            btc_balance = accounts.get("BTC", 0)
            print(f"BTC Available: {btc_balance}")

            if btc_balance < 0.01:
                trade = client.place_order(
                    product_id="BTC-USD",
                    side="buy",
                    order_type="market",
                    size="0.001"
                )
                print(f"🚀 Executed BUY trade: {trade}")
        except Exception as e:
            print("⚠️ Bot error:", e)

        time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

# Simple HTTP server for uptime
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nija bot is running 🚀".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
