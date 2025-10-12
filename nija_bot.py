# Put this at the very top of nija_bot.py
import os
# prefer API_KEY/API_SECRET for now (safer for debugging)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
if API_KEY and API_SECRET:
    print("Using API_KEY + API_SECRET for authentication (recommended for debugging).")
    # Create client using RESTClient later in code with these values.
else:
    print("API_KEY/API_SECRET not found — will try PEM (if provided).")

#!/usr/bin/env python3
# nija_bot.py — debug-friendly Coinbase Advanced client starter
# Note for kids: this file tries to safely connect to Coinbase and will NOT place live trades
# unless you explicitly set LIVE_TRADING=true in environment variables.

import os
import base64
import tempfile
import traceback
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Try import from coinbase-advanced-py package
try:
    from coinbase.rest import RESTClient
except Exception as e:
    raise SystemExit("❌ Missing coinbase-advanced-py library (ensure requirements.txt includes coinbase-advanced-py==1.8.2). Import error: " + repr(e))

# ===== Config from environment (set these in Render → Environment) =====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # optional multiline PEM (preferred if your UI supports multiline)
API_PEM_B64 = os.getenv("API_PEM_B64") # optional single-line base64 PEM
PORT = int(os.getenv("PORT", "8080"))
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() in ("1", "true", "yes")

# ===== Startup debug info (helpful) =====
print("=== STARTUP DEBUG INFO ===")
print("PORT:", PORT)
print("Have API_KEY:", bool(API_KEY))
print("Have API_SECRET:", bool(API_SECRET))
print("Have API_PEM (multiline):", bool(API_PEM))
print("Have API_PEM_B64 (base64):", bool(API_PEM_B64))
print("LIVE_TRADING:", LIVE_TRADING)
print("==========================")

# ===== Helpers =====
def _write_temp_pem(pem_bytes: bytes) -> str:
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush()
    tf.close()
    return tf.name

pem_path = None

# If multiline PEM provided, validate and write to temp file
if API_PEM:
    print("Using API_PEM (multiline). Showing first 3 lines for verification:")
    for i, line in enumerate(API_PEM.splitlines()[:3]):
        print(f"  line {i+1}: {line!r}")
    if "-----BEGIN" not in API_PEM or "-----END" not in API_PEM:
        print("⚠️ API_PEM does not contain PEM BEGIN/END markers — it may be malformed.")
    else:
        pem_path = _write_temp_pem(API_PEM.encode("utf-8"))
        print("✅ Wrote multiline PEM to:", pem_path)

# If base64 PEM provided, decode, inspect and write
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
        preview = decoded[:200]
        try:
            preview_text = preview.decode('utf-8', errors='replace')
        except Exception:
            preview_text = str(preview)
        print("Decoded PEM preview (first bytes):", preview_text.replace("\n", "\\n")[:200])
        if decoded.startswith(b"-----BEGIN"):
            pem_path = _write_temp_pem(decoded)
            print("✅ Decoded base64 -> wrote PEM to:", pem_path)
        else:
            # assume DER (binary) and wrap into PEM
            b64_der = base64.encodebytes(decoded)
            pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
            pem_path = _write_temp_pem(pem_bytes)
            print("✅ Wrapped DER -> PEM and wrote to:", pem_path)

# ===== Create RESTClient =====
client = None
try:
    if pem_path:
        print("Attempting RESTClient with key_file=", pem_path)
        client = RESTClient(key_file=pem_path)
    else:
        if not (API_KEY and API_SECRET):
            raise SystemExit("❌ Missing credentials: provide API_PEM/API_PEM_B64 OR API_KEY + API_SECRET in environment.")
        print("Attempting RESTClient with API_KEY/API_SECRET")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created successfully.")
except Exception as e:
    print("❌ Failed to create RESTClient. Exception type:", type(e).__name__)
    print("Exception message:", e)
    print("Full traceback:")
    traceback.print_exc()
    print("\n--- Helpful hints ---")
    print("1) If you used PEM/auth, ensure the PEM is the exact unencrypted key downloaded from https://cloud.coinbase.com/access/api")
    print("2) If you used API_KEY/API_SECRET, ensure they are correct and not wrapped in extra quotes or 'null'.")
    print("3) If you see PEM 'MalformedFraming' errors, your PEM is corrupted.")
    print("4) If you see JSON decode errors, some lib tried to parse empty JSON — check your secrets are not empty strings.")
    raise SystemExit("Cannot continue until the RESTClient is created. Check the logs above for details.")

# ===== Bot loop (SAFE: no automatic live trades unless LIVE_TRADING True) =====
def bot_loop():
    print("🚀 Bot loop started (safe mode). Will NOT place trades unless LIVE_TRADING=true)")
    while True:
        try:
            try:
                accounts = client.get_accounts()
            except Exception as e:
                print("⚠️ get_accounts() error:", type(e).__name__, e)
                accounts = None

            # show a short snapshot of accounts to logs
            s = str(accounts)
            print("Accounts snapshot (truncated):", (s[:800] + "...") if len(s) > 800 else s)

            # EXAMPLE trade logic (disabled by default):
            # If you *really* want to enable live buys, set LIVE_TRADING=true in environment and implement robust checks.
            if LIVE_TRADING:
                # WARNING: The code below is an example and may not match the client API exactly.
                # Replace with your validated safe trading code and add throttling/limits.
                try:
                    # Example: check BTC account and buy a tiny amount if available funds exist.
                    btc_account = None
                    if accounts:
                        for a in accounts:
                            # coinbase-advanced-py account structure may differ — adapt as needed
                            if isinstance(a, dict) and a.get("currency") == "BTC":
                                btc_account = a
                                break
                    if btc_account:
                        balance = float(btc_account.get("available", 0) or 0)
                        print("BTC available:", balance)
                        # Example threshold: if BTC < 0.001, attempt tiny buy (UNTESTED)
                        if balance < 0.001:
                            print("LIVE_TRADING is ON — placing a small buy order (example).")
                            # Replace with correct call for your client library:
                            # order = client.place_order(product_id="BTC-USD", side="buy", order_type="market", size="0.0005")
                            # print("Order result:", order)
                    else:
                        print("⚠️ BTC account not found.")
                except Exception as e:
                    print("⚠️ Error during live trading attempt:", type(e).__name__, e)
            else:
                # safe mode — no trades
                pass

        except Exception as e:
            print("⚠️ Outer bot error:", type(e).__name__, e)
        time.sleep(10)

threading.Thread(target=bot_loop, daemon=True).start()

# ===== HTTP health endpoint for Render =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("Nija bot running (safe mode)".encode("utf-8"))

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ HTTP health server listening on port {PORT}")
httpd.serve_forever()
