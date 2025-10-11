import os
import base64
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# -----------------------------
# Decode your API PEM key
# -----------------------------
API_PEM_B64 = os.getenv("API_PEM_B64")
if not API_PEM_B64:
    raise SystemExit("❌ Missing API_PEM_B64 environment variable")

decoded_pem = base64.b64decode(API_PEM_B64)
pem_path = "/tmp/nija_api_key.pem"
with open(pem_path, "wb") as f:
    f.write(decoded_pem)
print(f"✅ PEM decoded and written to {pem_path}")

# -----------------------------
# Import your bot logic
# -----------------------------
# Replace 'nija_bot_main' with your actual bot module filename (without .py)
from nija_bot_main import start_bot  

# Start the bot in a separate thread
threading.Thread(target=lambda: start_bot(pem_path), daemon=True).start()

# -----------------------------
# Minimal HTTP server (Render requires at least one open port)
# -----------------------------
PORT = int(os.getenv("PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running!")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
