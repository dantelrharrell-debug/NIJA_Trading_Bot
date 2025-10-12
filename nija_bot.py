#!/usr/bin/env python3
"""
nija_bot.py - debug-friendly safe starter (paste whole file)

Behavior:
 - Uses API_KEY + API_SECRET for auth (recommended while debugging PEM).
 - Shows debug info about environment values.
 - Does NOT place real trades unless LIVE_TRADING is set to "true".
 - Simple HTTP server so Render sees a listening port.
"""

import os, time, threading, base64, tempfile, traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== CONFIG / ENV =====
PORT = int(os.getenv("PORT", "8080"))
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # optional multiline PEM (NOT used by default)
API_PEM_B64 = os.getenv("API_PEM_B64") # optional base64 PEM (NOT used by default)
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"

# ===== IMPORT COINBASE CLIENT =====
try:
    # prefer the modern REST client import
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except Exception as e:
    print("❌ Failed importing coinbase.rest:", type(e).__name__, e)
    raise SystemExit("Install coinbase-advanced-py in requirements.txt and redeploy")

# ===== DEBUG PRINTS (helpful) =====
print("=== STARTUP DEBUG INFO ===")
print("PORT:", PORT)
print("Have API_KEY:", bool(API_KEY), "len:", len(API_KEY or ""))
print("Have API_SECRET:", bool(API_SECRET), "len:", len(API_SECRET or ""))
print("Have API_PEM (multiline):", bool(API_PEM))
print("Have API_PEM_B64 (base64):", bool(API_PEM_B64))
print("LIVE_TRADING:", LIVE_TRADING)
print("===========================")

# Helpful quick PEM preview if provided (but we will NOT use PEM by default)
def _preview_pem_from_b64(b64: str):
    try:
        clean = ''.join(b64.strip().split())
        pad = len(clean) % 4
        if pad:
            clean += '=' * (4 - pad)
        decoded = base64.b64decode(clean)
        # show first 200 bytes decoded (safe preview, do not post private key)
        preview = decoded[:200].decode('utf-8', errors='replace')
        return preview.replace("\n", "\\n")[:400]
    except Exception as e:
        return f"PEM base64 decode error: {e}"

if API_PEM_B64:
    print("API_PEM_B64 preview:", _preview_pem_from_b64(API_PEM_B64) )

# ===== CLIENT CREATION (FORCING API_KEY / API_SECRET) =====
client = None
try:
    if API_KEY and API_SECRET:
        # SAFE: prefer api_key/api_secret while debugging PEM issues
        print("Using API_KEY + API_SECRET for authentication (recommended).")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient created with API_KEY/API_SECRET")
    else:
        # No API_KEY/SECRET set — attempt PEM only if provided (less common)
        if API_PEM:
            # write multiline PEM to a temp file
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
            tf.write(API_PEM.encode("utf-8"))
            tf.flush(); tf.close()
            print("Wrote API_PEM to", tf.name)
            client = RESTClient(key_file=tf.name)
            print("✅ RESTClient created with multiline PEM")
        elif API_PEM_B64:
            # decode base64 and write to file
            clean = ''.join(API_PEM_B64.strip().split())
            pad = len(clean) % 4
            if pad:
                clean += '=' * (4 - pad)
            decoded = base64.b64decode(clean)
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
            tf.write(decoded); tf.flush(); tf.close()
            print("Wrote API_PEM_B64 decoded ->", tf.name)
            client = RESTClient(key_file=tf.name)
            print("✅ RESTClient created with API_PEM_B64")
        else:
            raise SystemExit("Missing API_KEY/API_SECRET and no PEM provided. Add secrets and redeploy.")
except Exception as e:
    print("❌ Failed to create RESTClient:", type(e).__name__, e)
    traceback.print_exc()
    # Helpful hints for the user (short)
    print("\nHints:")
    print(" - Make sure your API_KEY and API_SECRET are exact (no extra quotes/newlines).")
    print(" - If using PEM, create a single-line base64 with: base64 -w0 coinbase_private_key.pem")
    print(" - For now: the easiest is to set API_KEY and API_SECRET in Render Secrets and redeploy.")
    raise SystemExit("Cannot continue until RESTClient is created")

# ===== SAFE BOT LOOP (does NOT trade unless LIVE_TRADING true) =====
def bot_loop():
    print("🚀 Bot loop started (safe mode). LIVE_TRADING =", LIVE_TRADING)
    while True:
        try:
            # Fetch accounts (may be list/dict depending on client)
            try:
                accounts = client.get_accounts()
            except Exception as e:
                print("⚠️ get_accounts() error:", type(e).__name__, e)
                accounts = None
            # Print a truncated snapshot so logs stay small
            print("Accounts snapshot (truncated):", str(accounts)[:400])

            # If LIVE_TRADING is true, you can add real order logic here.
            if LIVE_TRADING:
                # Example (VERY RUDIMENTARY) - DO NOT ENABLE UNLESS YOU KNOW WHAT IT DOES
                print("LIVE_TRADING is ON. No automatic strategy is included in this template.")
                # Example placeholder: client.place_order(...)

        except Exception as e:
            print("⚠️ Bot outer error:", type(e).__name__, e)
        time.sleep(10)

# Start background thread
threading.Thread(target=bot_loop, daemon=True).start()

# ===== Simple HTTP server for Render health check =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        msg = f"Nija bot running. LIVE_TRADING={LIVE_TRADING}"
        self.wfile.write(msg.encode("utf-8"))

httpd = HTTPServer(("0.0.0.0", PORT), Handler)
print(f"✅ HTTP health server listening on port {PORT}")
httpd.serve_forever()
