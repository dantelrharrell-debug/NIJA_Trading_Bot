#!/usr/bin/env python3
import subprocess
import sys

# ---------- Ensure coinbase_advanced_py is installed ----------
try:
    from coinbase_advanced_py import Client
except ModuleNotFoundError:
    print("⚠️ coinbase_advanced_py not found, installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "coinbase-advanced-py==1.8.2"])
    print("✅ coinbase_advanced_py installed, retrying import...")
    from coinbase_advanced_py import Client

# ---------- Load environment variables ----------
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing Coinbase API_KEY or API_SECRET")

# ---------- Initialize Coinbase client ----------
client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized!")

# ---------- Example: check balances ----------
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("⚠️ Error fetching balances:", e)
