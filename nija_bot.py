import os, base64, tempfile
from coinbase.rest import RESTClient

# Prefer raw multiline PEM if available
API_PEM = os.getenv("API_PEM")
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

def _write_bytes_to_temp(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

if API_PEM:
    # API_PEM is full PEM text (with BEGIN/END), write as-is
    pem_temp_path = _write_bytes_to_temp(API_PEM.encode('utf-8'))
    print("✅ Wrote PEM (from API_PEM) to", pem_temp_path)
elif API_PEM_B64:
    # clean + pad, then base64-decode
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += '=' * (4 - pad)
    decoded = base64.b64decode(clean)

    # If decoded is already ascii PEM text:
    if decoded.startswith(b"-----BEGIN"):
        pem_temp_path = _write_bytes_to_temp(decoded)
        print("✅ Wrote PEM (decoded base64 -> PEM text) to", pem_temp_path)
    else:
        # decoded is DER binary — wrap in PEM
        b64_der = base64.encodebytes(decoded)  # adds newlines
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
        pem_temp_path = _write_bytes_to_temp(pem_bytes)
        print("✅ Wrote PEM (wrapped DER -> PEM) to", pem_temp_path)
else:
    raise SystemExit("❌ Missing API_PEM or API_PEM_B64 env var")

# Use pem_temp_path when constructing client: do NOT pass api_key/api_secret together with key_file
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if pem_temp_path:
    # Option A: use key_file (recommended if you used PEM)
    client = RESTClient(key_file=pem_temp_path)
    print("✅ RESTClient created with key_file")
else:
    # Fallback: use API_KEY + API_SECRET
    if not (API_KEY and API_SECRET):
        raise SystemExit("❌ Need API_KEY+API_SECRET if no PEM")
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created with API_KEY/API_SECRET")

import os, base64

# ✅ Decode private key at runtime
private_key_data = os.getenv("PRIVATE_KEY")
if not private_key_data:
    raise SystemExit("❌ PRIVATE_KEY not set")

with open("coinbase_private_key.pem", "wb") as f:
    f.write(base64.b64decode(private_key_data))

import os, base64, tempfile
import coinbase_advanced_py as cb   # library name to import

# decode base64 PEM if you have one — optional
API_PEM_B64 = os.getenv("API_PEM_B64")
if API_PEM_B64:
    # ensure padding & clean
    s = ''.join(API_PEM_B64.strip().split())
    pad = len(s) % 4
    if pad: s += '=' * (4 - pad)
    pem_bytes = base64.b64decode(s)
    pem_path = "/tmp/nija_api_key.pem"
    with open(pem_path, "wb") as f:
        f.write(pem_bytes)
    print("✅ Wrote PEM to", pem_path)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# create client - adjust to library usage; coinbase-advanced-py offers RESTClient in coinbase.rest
from coinbase.rest import RESTClient
client = RESTClient(key_file=pem_path) if API_PEM_B64 else RESTClient(api_key=API_KEY, api_secret=API_SECRET)

print("✅ Coinbase client created, starting bot...")
# ...rest of bot logic

try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase_advanced_py not installed! Check requirements.txt")

# nija_bot.py

import os
import base64
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ✅ Coinbase library
import coinbase_advanced_py as cb

# =========================
# Decode PEM key if provided
# =========================
API_PEM_B64 = os.getenv("API_PEM_B64")
if API_PEM_B64:
    decoded = base64.b64decode(API_PEM_B64)
    pem_path = "/tmp/nija_api_key.pem"
    with open(pem_path, "wb") as f:
        f.write(decoded)
    print(f"🔑 PEM key decoded and written to {pem_path}")

# =========================
# Initialize Coinbase client
# =========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables")

client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# =========================
# Trading bot logic
# =========================
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            balances = client.get_account_balances()  # Example
            print("💰 Balances:", balances)
        except Exception as e:
            print("⚠️ Error in bot loop:", e)
        time.sleep(5)  # Adjust as needed

# Start bot in a background thread
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
