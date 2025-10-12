# nija_bot.py
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Coinbase package
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase_advanced_py not installed or not visible:", e)

# ======================
# Config
# ======================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", 8080))

if not (API_KEY and API_SECRET):
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# ======================
# Initialize Coinbase client
# ======================
client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# ======================
# Bot logic
# ======================
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            balances = client.get_account_balances()
            print("💰 Balances:", balances)
        except Exception as e:
            print("⚠️ Bot loop error:", e)
        time.sleep(10)  # adjust frequency as needed

# run bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# ======================
# Minimal HTTP server for Render
# ======================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
