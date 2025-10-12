# nija_bot.py

try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

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

# ==== Helper to write PEM file ====
def _write_bytes(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

pem_path = None
if API_PEM:
    pem_path = _write_bytes(API_PEM.encode("utf-8"))
    print("✅ Wrote PEM from API_PEM ->", pem_path)
elif API_PEM_B64:
    decoded = base64.b64decode(''.join(API_PEM_B64.strip().split()))
    pem_path = _write_bytes(decoded)
    print("✅ Wrote decoded PEM ->", pem_path)
else:
    print("ℹ️ No PEM provided; will use API_KEY/API_SECRET")

# ==== Initialize Coinbase REST client ====
client = None
if pem_path:
    client = RESTClient(key_file=pem_path)
    print("✅ RESTClient initialized with PEM")
else:
    if not (API_KEY and API_SECRET):
        raise SystemExit("❌ Missing credentials: set API_PEM/API_PEM_B64 or API_KEY+API_SECRET")
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient initialized with API_KEY/API_SECRET")

# ==== Bot loop ====
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = client.get_accounts()
            print("💰 Accounts:", accounts[:1] if isinstance(accounts, (list, tuple)) else accounts)
        except Exception as e:
            print("⚠️ Bot loop error:", type(e).__name__, e)
        time.sleep(10)

threading.Thread(target=start_bot, daemon=True).start()

# ==== Minimal web server for Render ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
