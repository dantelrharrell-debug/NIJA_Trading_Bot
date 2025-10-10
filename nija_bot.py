#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

# --------------------------------------------
# Ensure vendor folder is in sys.path (for Render)
# --------------------------------------------
ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

# --------------------------------------------
# Load environment variables
# --------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file (if present)")
except Exception:
    print("ℹ️ python-dotenv not found or .env missing (OK on Render)")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables!")
    if not DRY_RUN:
        raise SystemExit(1)

# --------------------------------------------
# Import coinbase_advanced_py functions
# --------------------------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py (function-based API)")
except ModuleNotFoundError:
    print("❌ Module coinbase_advanced_py not found in vendor or site-packages")
    raise SystemExit(1)

# --------------------------------------------
# Example: Fetch accounts/balances
# --------------------------------------------
try:
    accounts = cb.get_accounts(api_key=API_KEY, api_secret=API_SECRET)
    print("💰 Accounts/balances:")
    for acc in accounts:
        print(f" - {acc['currency']}: {acc['available']} available")
except Exception as e:
    print("❌ Failed to fetch accounts:", type(e).__name__, e)

# --------------------------------------------
# Main bot loop (placeholder for trading logic)
# --------------------------------------------
try:
    while True:
        print(f"✅ Nija bot heartbeat — DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX}")
        # Example: you could call cb.get_account_balances() here if needed
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Nija bot stopped by user")
