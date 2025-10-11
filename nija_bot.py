# preferred
from coinbase.rest import RESTClient

# nija_bot.py
import os, base64, tempfile, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from coinbase.rest import RESTClient

# ==== Config ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # multiline PEM (preferred if UI supports it)
API_PEM_B64 = os.getenv("API_PEM_B64") # single-line base64 PEM (alternative)
PORT = int(os.getenv("PORT", "8080"))

pem_path = None

def _write_bytes(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

# Try multiline PEM first
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
        # assume DER; wrap into PEM
        b64_der = base64.encodebytes(decoded)  # newline safe
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
        pem_path = _write_bytes(pem_bytes)
        print("✅ Wrote wrapped DER->PEM ->", pem_path)
else:
    print("ℹ️ No PEM provided via API_PEM/API_PEM_B64; will try API_KEY/API_SECRET")

# Create REST client: prefer key_file if present; otherwise fallback to API key/secret
client = None
try:
    if pem_path:
        # Use PEM file (do NOT pass api_key/api_secret at same time)
        client = RESTClient(key_file=pem_path)
        print("✅ RESTClient created with key_file")
    else:
        if not (API_KEY and API_SECRET):
            raise SystemExit("❌ Missing credentials: set API_PEM/API_PEM_B64 or API_KEY+API_SECRET")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient created with API_KEY/API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to create RESTClient: {type(e).__name__} {e}")

# A simple bot loop (replace with your logic)
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = client.get_accounts()
            print("Accounts:", accounts[:1] if isinstance(accounts, (list,tuple)) else accounts)
        except Exception as e:
            print("⚠️ bot loop error:", type(e).__name__, e)
        time.sleep(10)

# start bot in background thread
threading.Thread(target=start_bot, daemon=True).start()

# minimal web server so Render detects a listen port (if running as web service)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ listening on port {PORT}")
httpd.serve_forever()
