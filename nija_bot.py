try:
    from coinbase.rest import RESTClient
    print("✅ Coinbase RESTClient ready")
except ImportError as e:
    raise SystemExit("❌ Coinbase RESTClient not installed:", e)

#!/usr/bin/env python3
# nija_bot.py

# ==== Import Coinbase REST safely ====
try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

# ==== Standard imports ====
import os
import base64
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==== Config ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # multiline PEM (preferred)
API_PEM_B64 = os.getenv("API_PEM_B64") # base64 PEM (alternative)
PORT = int(os.getenv("PORT", "8080"))

# ==== Prepare PEM file if provided ====
pem_path = None
if API_PEM:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(API_PEM.encode("utf-8"))
    tf.flush()
    tf.close()
    pem_path = tf.name
    print("✅ Wrote PEM from API_PEM ->", pem_path)
elif API_PEM_B64:
    decoded = base64.b64decode(API_PEM_B64)
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(decoded)
    tf.flush()
    tf.close()
    pem_path = tf.name
    print("✅ Wrote PEM from API_PEM_B64 ->", pem_path)
else:
    print("ℹ️ No PEM provided, will use API_KEY/API_SECRET if available")

# ==== Create RESTClient ====
if pem_path:
    client = RESTClient(key_file=pem_path)
    print("✅ RESTClient created with key_file")
else:
    if not (API_KEY and API_SECRET):
        raise SystemExit("❌ Missing API credentials: set API_PEM/API_PEM_B64 or API_KEY+API_SECRET")
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created with API_KEY/API_SECRET")

# ==== Simple bot loop (replace with your trading logic) ====
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = client.get_accounts()
            if isinstance(accounts, (list, tuple)):
                print("Accounts sample:", accounts[:1])
            else:
                print("Accounts:", accounts)
        except Exception as e:
            print("⚠️ Bot loop error:", type(e).__name__, e)
        time.sleep(10)

# Start bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# ==== Minimal web server so Render detects a port ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
