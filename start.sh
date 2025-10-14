#!/bin/bash

# 1️⃣ Activate the virtual environment
source "$PWD/.venv/bin/activate"

# 2️⃣ Upgrade pip (safe, idempotent)
python3 -m pip install --upgrade pip

# 3️⃣ Install all dependencies
python3 -m pip install -r requirements.txt

# 4️⃣ Run the bot with debug info
echo "🚀 Starting Nija bot..."

python3 - <<'PYTHON'
import os
import sys
import coinbase_advanced_py as cb
from dotenv import load_dotenv

# Print debug info
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

# Run main bot logic
import nija_bot
PYTHON
