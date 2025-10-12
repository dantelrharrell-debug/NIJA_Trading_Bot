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
API_PEM = os.getenv("API_PEM")          # optional multiline PEM
API_PEM_B64 = os.getenv("API_PEM_B64")  # optional base64 PEM
PORT = int(os.getenv("PORT", "8080"))

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

# ==== Initialize Client ====
client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

# ==== Bot Loop ====
def bot_loop():
    while True:
        try:
            accounts = client.get_accounts()
            print("Accounts:", accounts[:1] if isinstance(accounts, list) else accounts)
        except Exception as e:
            print("⚠️ Bot error:", type(e).__name__, e)
        time.sleep(10)  # adjust polling frequency as needed

threading.Thread(target=bot_loop, daemon=True).start()

# ==== Simple HTTP Server for Uptime ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        # Encode UTF-8 to allow emojis
        self.wfile.write("Nija bot is running 🚀".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
def check_coinbase():
    try:
        accounts = client.get_accounts()
        print("✅ Coinbase connection OK. First account:", accounts[0] if accounts else "No accounts found")
    except Exception as e:
        print("❌ Coinbase connection failed:", type(e).__name__, e)

