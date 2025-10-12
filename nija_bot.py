#!/usr/bin/env python3
# nija_bot.py - ready-to-paste

import os
import base64
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Prefer this import (the package you installed exposes `coinbase.rest`)
try:
    from coinbase.rest import RESTClient
except Exception as e:
    raise SystemExit("❌ Missing coinbase package or import error. Ensure requirements.txt contains coinbase-advanced-py==1.8.2. Error: " + repr(e))

# Config (set these on Render -> Environment)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # optional: full multiline PEM
API_PEM_B64 = os.getenv("API_PEM_B64") # optional: base64-encoded PEM (single line)
PORT = int(os.getenv("PORT", "8080"))

# Helper to write bytes to a named temporary file
def _write_temp_pem(pem_bytes: bytes) -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush()
    tf.close()
    return tf.name

pem_temp_path = None

# Try multiline PEM first
if API_PEM:
    pem_temp_path = _write_temp_pem(API_PEM.encode("utf-8"))
    print("✅ Wrote PEM from API_PEM ->", pem_temp_path)
elif API_PEM_B64:
    # Clean whitespace/newlines that might be introduced by UI / copy paste
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += '=' * (4 - pad)
    try:
        decoded = base64.b64decode(clean)
    except Exception as e:
        raise SystemExit("❌ API_PEM_B64 could not be base64-decoded: " + repr(e))

    # If decoded already starts with PEM header, use it; otherwise wrap DER->PEM
    if decoded.startswith(b"-----BEGIN"):
        pem_temp_path = _write_temp_pem(decoded)
        print("✅ Decoded base64 -> PEM written to", pem_temp_path)
    else:
        b64_der = base64.encodebytes(decoded)  # safe newlines
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
        pem_temp_path = _write_temp_pem(pem_bytes)
        print("✅ Wrapped DER->PEM ->", pem_temp_path)

# Create RESTClient — **do not** pass api_key/api_secret together with key_file
client = None
try:
    if pem_temp_path:
        client = RESTClient(key_file=pem_temp_path)
        print("✅ RESTClient created with PEM key file")
    else:
        if not (API_KEY and API_SECRET):
            raise SystemExit("❌ Missing credentials. Provide API_PEM/API_PEM_B64 OR API_KEY + API_SECRET in Render environment.")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient created with API_KEY/API_SECRET")
except Exception as e:
    raise SystemExit("❌ Failed to create RESTClient: " + repr(e))

# Bot loop (replace logic with your strategy). This shows accounts for debugging.
def bot_loop():
    print("🚀 Nija bot loop starting")
    while True:
        try:
            # the library returns list/dict depending on wrappers; handle both
            try:
                accounts = client.get_accounts()
            except Exception as e:
                # If get_accounts fails, print the error and continue
                print("⚠️ get_accounts error:", type(e).__name__, e)
                accounts = None

            print("Accounts snapshot (truncated):", str(accounts)[:400])

            # Example: naive BTC check - adapt to your real data structure / logic
            try:
                if isinstance(accounts, (list, tuple)):
                    btc = next((a for a in accounts if a.get("currency") == "BTC" or a.get("asset")=="BTC"), None)
                    available = float(btc.get("available", 0)) if btc else 0.0
                elif isinstance(accounts, dict):
                    available = float(accounts.get("BTC", 0))
                else:
                    available = 0.0
                print(f"BTC available: {available}")
            except Exception:
                available = 0.0

            # Example trade (VERY simple, remove or change before real money)
            if available < 0.01:
                print("Info: BTC < 0.01, skipping auto-trade in this example (enable only after testing).")
                # REMOVE or REPLACE the following block with your real order code if you really want live trades:
                # trade = client.place_order(product_id="BTC-USD", side="buy", order_type="market", size="0.001")
                # print("🚀 Executed BUY:", trade)

        except Exception as e:
            print("⚠️ Bot loop outer error:", type(e).__name__, e)

        time.sleep(10)

# Start bot thread
threading.Thread(target=bot_loop, daemon=True).start()

# Minimal HTTP server so Render sees an open port
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nija bot is running".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Listening on port {PORT}  (URL should be your Render service URL)")
httpd.serve_forever()
