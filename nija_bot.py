import sys
import os

# Make sure Python uses the virtual environment
venv_site = os.path.join(os.path.dirname(__file__), ".venv/lib/python3.13/site-packages")
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

import os
from coinbase_advanced_py import Client
from cryptography.hazmat.primitives import serialization

# -----------------------------
# STEP 1: Load your private key
# -----------------------------
pem_path = os.path.join(os.path.dirname(__file__), "coinbase_key.pem")
with open(pem_path, "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
    )

# -----------------------------
# STEP 2: Set your API key
# -----------------------------
API_KEY = os.getenv("API_KEY")  # Go to Render dashboard → Secrets → Add your API_KEY
API_SECRET = private_key         # This is loaded from the PEM automatically

# -----------------------------
# STEP 3: Connect Nija
# -----------------------------
client = Client(API_KEY, API_SECRET)

# Quick balance check to make sure it works
balances = client.get_account_balances()
print("✅ Nija connected! Balances:", balances)

#!/usr/bin/env python3

import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==== Coinbase Import ====
try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

# ==== Config ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", "8080"))

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

# ==== Initialize Client ====
client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

# ==== Bot Loop with Live Trade Logging ====
def bot_loop():
    while True:
        try:
            accounts = client.get_accounts()
            print("Accounts:", accounts[:1] if isinstance(accounts, list) else accounts)
            
            # Example: Check BTC balance and place a simple buy if you want (replace with your logic)
            btc_account = next((a for a in accounts if a['currency'] == 'BTC'), None)
            if btc_account:
                balance = float(btc_account['available'])
                print(f"BTC Available: {balance}")

                # Example trade logic (for demonstration; replace with your strategy)
                if balance < 0.01:  # if BTC < 0.01, buy 0.001 BTC
                    trade = client.place_order(
                        product_id="BTC-USD",
                        side="buy",
                        order_type="market",
                        size="0.001"
                    )
                    print(f"🚀 Executed BUY trade: {trade}")
            else:
                print("⚠️ BTC account not found")
        except Exception as e:
            print("⚠️ Bot error:", type(e).__name__, e)

        time.sleep(10)  # adjust polling frequency as needed

threading.Thread(target=bot_loop, daemon=True).start()

# ==== Simple HTTP Server for Uptime ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nija bot is running 🚀".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
