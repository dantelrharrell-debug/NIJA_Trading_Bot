#!/bin/bash

# Activate virtual environment
source "$PWD/.venv/bin/activate"

# Upgrade pip safely
python3 -m pip install --upgrade pip

# Install dependencies
python3 -m pip install -r requirements.txt

echo "🚀 Starting Nija bot with auto-restart..."

# Infinite loop to keep the bot running
while true; do
    echo "🔁 Launching bot..."
    
    python3 - <<'PYTHON'
import os
import sys
import coinbase_advanced_py as cb
from dotenv import load_dotenv

# Debug info
print("Python executable:", sys.executable)
print("Python path:", sys.path)
print("Current working dir:", os.getcwd())

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in .env")

# Connect to Coinbase
client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# Optional: check balances
balances = client.get_account_balances()
print("💰 Balances:", balances)

# Run main bot
import nija_bot
PYTHON

    echo "⚠️ Bot exited unexpectedly, restarting in 5 seconds..."
    sleep 5
done
