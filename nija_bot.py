#!/usr/bin/env python3
import os, time, threading, base64, tempfile, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# Try import coinbase library
try:
    from coinbase.rest import RESTClient
except Exception as e:
    raise SystemExit("Missing coinbase library. Ensure requirements.txt includes coinbase-advanced-py==1.8.2. Import error: " + repr(e))

# === Config / Debug print ===
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")
API_PEM_B64 = os.getenv("API_PEM_B64")
PORT = int(os.getenv("PORT", "10000"))
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() in ("1","true","yes")

print("=== STARTUP DEBUG ===")
print("Have API_KEY:", bool(API_KEY))
print("Have API_SECRET:", bool(API_SECRET))
print("Have API_PEM:", bool(API_PEM))
print("Have API_PEM_B64:", bool(API_PEM_B64))
print("LIVE_TRADING:", LIVE_TRADING)

# helper write temp PEM
def _write_temp_pem(pem_bytes: bytes) -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush(); tf.close()
    return tf.name

client = None
try:
    # Prefer API_KEY/API_SECRET because it's fast to test
    if API_KEY and API_SECRET:
        print("Using API_KEY + API_SECRET for authentication (recommended for testing).")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    else:
        # Use PEM (multiline)
        if API_PEM:
            print("Using API_PEM (multiline).")
            pem_path = _write_temp_pem(API_PEM.encode("utf-8"))
            print("Wrote PEM to", pem_path)
            client = RESTClient(key_file=pem_path)
        elif API_PEM_B64:
            print("Using API_PEM_B64 (base64). Decoding and writing PEM.")
            clean = ''.join(API_PEM_B64.strip().split())
            pad = len(clean) % 4
            if pad:
                clean += '=' * (4 - pad)
            decoded = base64.b64decode(clean)
            # if decoded looks like DER (no BEGIN header) wrap it
            if not decoded.startswith(b"-----BEGIN"):
                b64_der = base64.encodebytes(decoded)
                decoded = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
            pem_path = _write_temp_pem(decoded)
            print("Wrote decoded PEM to", pem_path)
            client = RESTClient(key_file=pem_path)
        else:
            raise SystemExit("Missing credentials: set API_KEY/API_SECRET or API_PEM/API_PEM_B64 in Render env")
    print("✅ RESTClient created")
except Exception as e:
    print("❌ Failed to create RESTClient:", type(e).__name__, e)
    traceback.print_exc()
    raise SystemExit("Cannot continue until RESTClient is created. Fix env and redeploy.")

# Bot loop (safe — does not execute trades automatically)
def bot_loop():
    print("🚀 Bot loop started (safe mode).")
    while True:
        try:
            try:
                accounts = client.get_accounts()
            except Exception as e:
                print("⚠️ get_accounts() error:", type(e).__name__, e)
                accounts = None
            print("Accounts snapshot (truncated):", str(accounts)[:600])
        except Exception as e:
            print("⚠️ Outer bot error:", type(e).__name__, e)
        time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

# Minimal HTTP server so Render knows it's alive
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running (safe mode)")

httpd = HTTPServer(("", PORT), Handler)
print("✅ HTTP server on port", PORT)
httpd.serve_forever()
