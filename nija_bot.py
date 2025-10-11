import os
import base64
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from coinbase.rest import RESTClient

PORT = int(os.getenv("PORT", "8080"))

# 🔐 Load Coinbase PEM credentials
API_PEM_B64 = os.getenv("API_PEM_B64")
if not API_PEM_B64:
    raise SystemExit("❌ Missing API_PEM_B64 environment variable")

# 🔓 Decode PEM and write to temporary file
def decode_pem(b64_str: str) -> str:
    try:
        clean = ''.join(b64_str.strip().split())
        pad = len(clean) % 4
        if pad:
            clean += '=' * (4 - pad)
        decoded = base64.b64decode(clean)
        if decoded.startswith(b"-----BEGIN"):
            pem_bytes = decoded
        else:
            # wrap DER to PEM
            pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + base64.encodebytes(decoded) + b"-----END PRIVATE KEY-----\n"
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(pem_bytes)
        tf.flush()
        tf.close()
        print("✅ Wrote PEM to", tf.name)
        return tf.name
    except Exception as e:
        raise SystemExit(f"❌ Failed to decode/write PEM: {e}")

pem_path = decode_pem(API_PEM_B64)

# --- Start Coinbase REST client
try:
    client = RESTClient(key_file=pem_path)
    print("✅ RESTClient created using PEM key")
    # Test authentication
    balances = client.get_account_balances()
    print("💰 Coinbase balances:", balances)
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {e}")

# --- Start a simple web server to keep Render happy
def start_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Nija bot is running!")
    httpd = HTTPServer(("", PORT), Handler)
    print(f"✅ Web server listening on port {PORT}")
    httpd.serve_forever()

threading.Thread(target=start_server, daemon=True).start()

# --- Place your main bot logic here
def start_bot():
    print("🚀 Nija bot logic starts here")
    # Example: do a dummy trade or run your trading loop
    while True:
        pass  # replace with trading loop

# Run the bot in a separate thread so web server stays alive
threading.Thread(target=start_bot, daemon=True).start()
