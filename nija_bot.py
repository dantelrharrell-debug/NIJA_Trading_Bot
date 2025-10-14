#!/usr/bin/env python3

import sys
import subprocess
import os

# ------------------------------
# Install coinbase_advanced_py if missing
# ------------------------------
try:
    import coinbase_advanced_py
except ModuleNotFoundError:
    print("⚠️ coinbase_advanced_py not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "coinbase-advanced-py==1.8.2"])
    # Force Python to reload site-packages paths
    import importlib
    importlib.invalidate_caches()

# Now import Client safely
from coinbase_advanced_py import Client

# ------------------------------
# Load environment variables
# ------------------------------
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "python-dotenv==1.1.1"])
    import importlib
    importlib.invalidate_caches()
    from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing Coinbase API_KEY or API_SECRET in .env")

# ------------------------------
# Initialize Coinbase client
# ------------------------------
client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized!")

# ------------------------------
# Fetch balances
# ------------------------------
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("⚠️ Error fetching balances:", e)
