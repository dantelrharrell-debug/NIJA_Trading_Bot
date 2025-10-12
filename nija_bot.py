try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase_advanced_py not installed or not visible:", e)

# nija_bot.py

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ✅ Make sure coinbase_advanced_py is installed in your requirements.txt
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase_advanced_py not installed or not visible:", e)

# ==== Config ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", "8080"))

if not (API_KEY and API_SECRET):
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# ==== Initialize Coinbase client ====
client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# ==== Bot loop ====
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            balances = client.get_account_balances()
            print("💰 Balances:", balances)
        except Exception as e:
            print("⚠️ Bot loop error:", type(e).__name__, e)
        time.sleep(10)  # Adjust your polling interval

# Run bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# ==== Minimal web server for Render health check ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
