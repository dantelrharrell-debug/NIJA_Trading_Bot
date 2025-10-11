import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import coinbase_advanced_py as cb
import time

# =========================
# Coinbase API Setup
# =========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables")

client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# =========================
# Your trading bot logic
# =========================
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            # Example: get balances (replace with your real trading logic)
            balances = client.get_account_balances()
            print("💰 Balances:", balances)
        except Exception as e:
            print("⚠️ Error in bot loop:", e)
        time.sleep(5)  # Adjust sleep for your trading frequency

# =========================
# Start bot in background thread
# =========================
threading.Thread(target=start_bot, daemon=True).start()

# =========================
# Minimal HTTP server for Render
# =========================
PORT = int(os.getenv("PORT", 8080))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running!")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
