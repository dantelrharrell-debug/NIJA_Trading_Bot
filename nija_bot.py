# nija_bot.py

try:
    from coinbase.rest import RESTClient
    print("✅ coinbase.rest import OK")
except ImportError as e:
    raise SystemExit("❌ coinbase.rest not installed or not visible:", e)

import os
import base64
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==== Config ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")         # multiline PEM
API_PEM_B64 = os.getenv("API_PEM_B64") # single-line base64 PEM
PORT = int(os.getenv("PORT", "8080"))

# ...rest of your bot logic...
