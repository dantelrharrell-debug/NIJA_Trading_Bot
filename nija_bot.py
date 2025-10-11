import os
import base64
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---- Step 1: Decode PEM and write to temp file ----
API_PEM_B64 = os.getenv("API_PEM_B64")
if not API_PEM_B64:
    raise SystemExit("❌ Missing API_PEM_B64 environment variable")

try:
    decoded_pem = base64.b64decode(API_PEM_B64)
    pem_text = decoded_pem.decode("utf-8")
    if not pem_text.startswith("-----BEGIN PRIVATE KEY-----"):
        raise ValueError("Decoded PEM does not start with expected header")
    
    # Write to a temporary file
    pem_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    pem_file.write(decoded_pem)
    pem_file.close()
    print(f"✅ PEM decoded and written to {pem_file.name}")
except Exception as e:
    raise SystemExit(f"❌ Failed to decode/write PEM: {e}")

# ---- Step 2: Import your bot ----
# Make sure start_bot(pem_path) is your bot's entry point accepting a PEM path
from nija_bot_logic import start_bot  # Replace with your actual bot module

# ---- Step 3: Start bot in a background thread ----
threading.Thread(target=start_bot, args=(pem_file.name,), daemon=True).start()
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
