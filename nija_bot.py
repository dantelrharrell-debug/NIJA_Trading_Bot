try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

# your existing bot code continues here...

try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

# nija_bot.py
import os
import base64
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ----------------------
# Try importing Coinbase client
# ----------------------
try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

# ----------------------
# Config: credentials
# ----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # multiline PEM (optional)
API_PEM_B64 = os.getenv("API_PEM_B64") # single-line base64 PEM (optional)
PORT = int(os.getenv("PORT", 8080))

# ----------------------
# Helper to write PEM file if needed
# ----------------------
def write_pem(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

pem_path = None
if API_PEM:
    pem_path = write_pem(API_PEM.encode("utf-8"))
elif API_PEM_B64:
    decoded = base64.b64decode(API_PEM_B64)
    pem_path = write_pem(decoded)

# ----------------------
# Initialize Coinbase REST client
# ----------------------
if pem_path:
    client = RESTClient(key_file=pem_path)
    print(f"✅ RESTClient initialized with PEM -> {pem_path}")
else:
    if not (API_KEY and API_SECRET):
        raise SystemExit("❌ Missing credentials: provide API_KEY/API_SECRET or API_PEM/API_PEM_B64")
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient initialized with API_KEY/API_SECRET")

# ----------------------
# Bot loop
# ----------------------
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = client.get_accounts()
            print("💰 Accounts:", accounts[:1] if isinstance(accounts, (list, tuple)) else accounts)
        except Exception as e:
            print("⚠️ Bot loop error:", type(e).__name__, e)
        time.sleep(10)  # adjust frequency

# Start bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# ----------------------
# Minimal web server (for Render to detect port)
# ----------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
