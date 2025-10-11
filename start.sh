#!/bin/bash

# =========================
# Activate virtual environment
# =========================
if [ -d ".venv" ]; then
    echo "🔹 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ Virtual environment not found, creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# =========================
# Ensure all requirements are installed
# =========================
echo "📦 Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# =========================
# Decode PEM if using API_PEM_B64
# =========================
if [ ! -f "/tmp/nija_api_key.pem" ] && [ ! -z "$API_PEM_B64" ]; then
    echo "🔑 Decoding API PEM..."
    python3 - <<END
import os, base64
decoded = base64.b64decode(os.getenv("API_PEM_B64"))
with open("/tmp/nija_api_key.pem", "wb") as f:
    f.write(decoded)
END
fi

# =========================
# Start the Nija bot
# =========================
echo "🚀 Starting Nija bot..."
./.venv/bin/python3 nija_bot.py
