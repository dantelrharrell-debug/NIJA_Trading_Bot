import os
import base64
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from coinbase.rest import RESTClient

# -------------------------------
# 🔐 Load Coinbase credentials
# -------------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")

if not all([API_KEY, API_SECRET, API_PEM_B64]):
    raise SystemExit("❌ Missing API_KEY, API_SECRET, or API_PEM_B64")

# -------------------------------
# 🔓 Decode PEM key and write temp file
# -------------------------------
pem_temp_path = None

def bytes_is_pem(b: bytes) -> bool:
    return b.startswith(b"-----BEGIN")

try:
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += '=' * (4 - pad)

    decoded = base64.b64decode(clean)

    if bytes_is_pem(decoded):
        pem_bytes = decoded
        print("Decoded input is PEM text.")
    else:
        print("Decoded input looks like DER/binary; converting to PEM wrapper.")
        b64_der = base64.encodebytes(decoded)
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"

    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush(); tf.close()
    pem_temp_path = tf.name
    print("✅ Wrote PEM to", pem_temp_path)

except Exception as e:
    raise SystemExit(f"❌ Failed to decode/write PEM: {type(e).__name__} {e}")

# -------------------------------
# 🤖 Bot main logic
# -------------------------------
def start_bot():
    try:
        # Use either API_KEY/API_SECRET or PEM file, not both
        client = RESTClient(key_file=pem_temp_path)
        print("✅ RESTClient created using key_file")
    except Exception as e:
        raise SystemExit(f"❌ Failed to start Coinbase client: {type(e).__name__} {e}")

    # --- Example bot loop (replace with your bot logic) ---
    import time
    while True:
        print("🤖 Nija bot running...")
        # Example: check balances or place trades here
        try:
            balances = client.get_account_balances()
            print("Balances:", balances)
        except Exception as e:
            print("⚠️ Error fetching balances:", e)
        time.sleep(60)  # Run every minute

# -------------------------------
# 🌐 Minimal HTTP server for Render
# -------------------------------
PORT = int(os.getenv("PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running!")

# Start bot in a separate thread
threading.Thread(target=start_bot, daemon=True).start()

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
