import os
import threading
import importlib.util
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------------------
# Config
# -------------------------------
PORT = int(os.getenv("PORT", "8080"))

# Automatically find the bot module
BOT_MODULE_NAME = None
BOT_FUNCTION_NAME = "start_bot"

for file in os.listdir("."):
    if file.endswith(".py") and file not in ("nija_bot.py", "__init__.py"):
        spec = importlib.util.spec_from_file_location("bot_module", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, BOT_FUNCTION_NAME):
            BOT_MODULE_NAME = file[:-3]  # remove .py
            break

if not BOT_MODULE_NAME:
    raise SystemExit("❌ No bot module with a 'start_bot()' function found in this folder!")

bot_module = importlib.import_module(BOT_MODULE_NAME)
print(f"✅ Loaded bot from {BOT_MODULE_NAME}.py")

# -------------------------------
# Start the bot in a background thread
# -------------------------------
threading.Thread(target=getattr(bot_module, BOT_FUNCTION_NAME), daemon=True).start()

# -------------------------------
# Minimal HTTP server for Render
# -------------------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nija bot is running!")

httpd = HTTPServer(("", PORT), Handler)
print(f"✅ Web server listening on port {PORT}")
httpd.serve_forever()
