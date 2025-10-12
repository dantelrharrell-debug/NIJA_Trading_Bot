#!/usr/bin/env python3
import sys
import importlib
import os
import base64
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================
# Debug & Environment Check
# ==========================
print("Python executable:", sys.executable)
print("Python sys.path[:8]:", sys.path[:8])
print("Coinbase spec:", importlib.util.find_spec("coinbase"))

try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except Exception as e:
    print("❌ coinbase.rest import failed:", type(e).__name__, e)
    raise

# ==========================
# Config / Credentials
# ==========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")          # multiline PEM
API_PEM_B64 = os.getenv("API_PEM_B64")  # single-line base64 PEM
PORT = int(os.getenv("PORT", "8080"))

# ==========================
# Helper: write bytes to temp PEM file
# ==========================
def _write_bytes(b: bytes):
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(b)
    tf.flush()
    tf.close()
    return tf.name

# ==========================
# Prepare PEM / DER if provided
# ==========================
pem_path = None

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
        # assume DER, wrap into PEM
        b64_der = base64.encodebytes(decoded)
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
        pem_path = _write_bytes(pem_bytes)
        print("✅ Wrote wrapped DER->PEM ->", pem_path)
else:
    print("ℹ️ No PEM provided; will try API_KEY/API_SECRET")

# ==========================
# Initialize RESTClient
# ==========================
client = None
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

# ==========================
# Bot Logic (background thread)
# ==========================
def start_bot():
    print("🚀 Nija bot started")
    while True:
        try:
            accounts = list(client.get_accounts())  # convert generator to list
            print("Accounts:", accounts[:1] if accounts else "No accounts")
        except Exception as e:
            print("⚠️ Bot loop error:", type(e).__name__, e)
        time.sleep(10)  # adjust frequency

threading.Thread(target=start_bot, daemon=True).start()

# ==========================
# Minimal HTTP server for Render
# ==========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running ✅")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}")
httpd.serve_forever()
