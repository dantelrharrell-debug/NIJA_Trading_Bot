import os
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---- Step 1: Verify PEM ----
API_PEM_B64 = os.getenv("API_PEM_B64")
if not API_PEM_B64:
    raise SystemExit("❌ Missing API_PEM_B64 environment variable")

try:
    decoded_pem = base64.b64decode(API_PEM_B64)
    pem_text = decoded_pem.decode("utf-8")
    if not pem_text.startswith("-----BEGIN PRIVATE KEY-----"):
        raise ValueError("Decoded PEM does not start with expected header")
    print("✅ PEM decoded successfully")
except Exception as e:
    raise SystemExit(f"❌ Failed to decode PEM: {e}")

# ---- Step 2: Import your bot ----
# Make sure start_bot() is the entry point of your trading bot
from nija_bot_logic import start_bot  # Replace with your actual bot module

# ---- Step 3: Start bot in a background thread ----
threading.Thread(target=start_bot, daemon=True).start()
print("🚀 Nija bot started in background thread")

# ---- Step 4: Minimal HTTP server to satisfy Render ----
PORT = int(os.getenv("PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running!")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
