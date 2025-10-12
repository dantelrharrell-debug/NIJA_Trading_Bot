# nija_bot.py
import os
import base64
import tempfile
import threading
import time
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
API_PEM = os.getenv("API_PEM")         # multiline PEM
API_PEM_B64 = os.getenv("API_PEM_B64") # single-line base64 PEM
PORT = int(os.getenv("PORT", "8080"))

pem_path = None

# ==== Helper: Write PEM file ====
def _write_bytes(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

# ==== Prepare PEM or fallback to key/secret ====
if API_PEM:
    pem_path = _write_bytes(API_PEM.encode("utf-8"))
    print("✅ Wrote PEM from API_PEM ->", pem_path)
elif API_PEM_B64:
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += '=' * (4 - pad)
    decoded = base64.b64decode(clean)
    if decoded.startswith(b"-----BEGIN"):
        pem_path = _write_bytes(decoded)
        print("✅ Wrote decoded PEM ->", pem_path)
    else:
        # Wrap DER into PEM
        b64_der = base64.encodebytes(decoded)
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
        pem_path = _write_bytes(pem_bytes)
        print("✅ Wrote wrapped DER->PEM ->", pem_path)
else:
    print("ℹ️ No PEM provided; will use API_KEY/API_SECRET")

# ==== Create REST client ====
try:
    if pem_path:
        client = RESTClient(key_file=pem_path)
        print("✅ RESTClient created with key_file")
    else:
        if not (API_KEY and API_SECRET):
            raise SystemExit("❌ Missing credentials: set API_PEM/API_PEM_B64 or API_KEY+API_SECRET")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient created with API_KEY/API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to create RESTClient: {type(e).__name__} {e}")

# ==== Bot logic ====
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = client.get_accounts()
            print("Accounts:", accounts[:1] if isinstance(accounts, (list, tuple)) else accounts)
        except Exception as e:
            print("⚠️ bot loop error:", type(e).__name__, e)
        time.sleep(10)

# Start bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# ==== Minimal web server for Render ====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ listening on port {PORT}")
httpd.serve_forever()
