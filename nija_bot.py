#!/usr/bin/env python3
# nija_bot.py - debug-friendly, safe client creation (paste entire file)

import os
import base64
import tempfile
import traceback
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Coinbase import
try:
    from coinbase.rest import RESTClient
except Exception as e:
    raise SystemExit("❌ Missing coinbase library. Ensure requirements.txt includes coinbase-advanced-py==1.8.2. Import error: " + repr(e))

# Config from environment (Render secrets)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # multiline PEM (preferred)
API_PEM_B64 = os.getenv("API_PEM_B64") # single-line base64 PEM alternative
PORT = int(os.getenv("PORT", "8080"))

print("=== STARTUP DEBUG INFO ===")
print("PORT:", PORT)
print("Have API_KEY:", bool(API_KEY))
print("Have API_SECRET:", bool(API_SECRET))
print("Have API_PEM (multiline):", bool(API_PEM))
print("Have API_PEM_B64 (base64):", bool(API_PEM_B64))

# helper
def _write_temp_pem(pem_bytes: bytes) -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush()
    tf.close()
    return tf.name

pem_path = None

# If multiline PEM provided, validate and write
if API_PEM:
    print("Using API_PEM (multiline). Showing first 3 lines for verification:")
    for i, line in enumerate(API_PEM.splitlines()[:10]):
        print(f"  line {i+1}: {line!r}")
    if "-----BEGIN" not in API_PEM or "-----END" not in API_PEM:
        print("⚠️ API_PEM does not contain BEGIN/END markers - likely malformed.")
    else:
        pem_path = _write_temp_pem(API_PEM.encode("utf-8"))
        print("✅ Wrote multiline PEM to:", pem_path)

# If only base64 provided, decode and inspect
elif API_PEM_B64:
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += '=' * (4 - pad)
    try:
        decoded = base64.b64decode(clean)
    except Exception as e:
        print("❌ Failed to base64-decode API_PEM_B64:", type(e).__name__, e)
        decoded = None

    if decoded:
        # print small preview
        preview = decoded[:200]
        try:
            preview_text = preview.decode('utf-8', errors='replace')
        except Exception:
            preview_text = str(preview)
        print("Decoded PEM preview:", preview_text.replace("\n", "\\n")[:200])
        if decoded.startswith(b"-----BEGIN"):
            pem_path = _write_temp_pem(decoded)
            print("✅ Decoded base64 -> wrote PEM to:", pem_path)
        else:
            # assume DER: wrap into PEM and write
            b64_der = base64.encodebytes(decoded)
            pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
            pem_path = _write_temp_pem(pem_bytes)
            print("✅ Wrapped DER->PEM and wrote to:", pem_path)

# If no PEM, we'll consider API_KEY/API_SECRET
if not pem_path:
    print("No PEM path. Using API_KEY/API_SECRET (if present).")

# Create client safely: only one auth method.
client = None
try:
    if pem_path:
        print("Attempting RESTClient with key_file=", pem_path)
        client = RESTClient(key_file=pem_path)
    else:
        if not (API_KEY and API_SECRET):
            raise SystemExit("❌ Missing credentials: provide API_PEM/API_PEM_B64 OR API_KEY + API_SECRET as Render secrets.")
        print("Attempting RESTClient with API_KEY/API_SECRET")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created (no exception thrown).")
except Exception as e:
    print("❌ Failed to create RESTClient. Exception type:", type(e).__name__)
    print("Exception message:", e)
    print("Full traceback:")
    traceback.print_exc()
    # Helpful troubleshooting hints
    print("\n--- Helpful hints ---")
    print("1) If you used PEM/auth, ensure the PEM is the exact unencrypted PEM downloaded from https://cloud.coinbase.com/access/api")
    print("2) If you used API_KEY/API_SECRET, make sure they are correct strings (no extra quotes, newlines, or JSON wrappers).")
    print("3) If you see 'MalformedFraming' or cryptography PEM errors, your PEM is corrupted or not a valid PEM.")
    print("4) If you see JSON decode errors, some library tried to parse empty content as JSON. Double-check API_SECRET or other env vars are not empty strings like '' or 'null'.")
    raise SystemExit("Cannot continue until the RESTClient is created. Check the logs above for details.")

# Minimal bot loop (safe — does not place orders by default)
def bot_loop():
    print("🚀 Bot loop started (safe mode).")
    while True:
        try:
            accounts = None
            try:
                accounts = client.get_accounts()
            except Exception as e:
                print("⚠️ get_accounts() raised:", type(e).__name__, e)
            print("Accounts snapshot (truncated):", str(accounts)[:500])

            # Example safe check - no real trading executed here.
            # Uncomment and modify ONLY after you confirm everything:
            # if should_place_trade():
            #     client.place_order(...)

        except Exception as e:
            print("⚠️ Outer bot error:", type(e).__name__, e)
        time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

# HTTP server for Render health
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nija bot running (safe mode)".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ HTTP health server listening on port {PORT}")
httpd.serve_forever()
