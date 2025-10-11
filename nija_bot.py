import os
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import coinbase_advanced_py as cb   # Only once, at the top

# =========================
# Decode your PEM key (if using one)
# =========================
API_PEM_B64 = os.getenv("API_PEM_B64")
if API_PEM_B64:
    decoded = base64.b64decode(API_PEM_B64)
    with open("/tmp/nija_api_key.pem", "wb") as f:
        f.write(decoded)
    print("✅ PEM key decoded and saved")

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
            balances = client.get_account_balances()
            print("💰 Balances:", balances)
        except Exception as e:
            print("⚠️ Error in bot loop:", e)
        time.sleep(5)  # Adjust for your trading frequency

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
