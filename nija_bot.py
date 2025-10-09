#!/usr/bin/env python3
import sys
import os

# -----------------------------
# 1️⃣ Add vendor folder to sys.path
# -----------------------------
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print(f"✅ Added vendor folder to sys.path: {VENDOR_DIR}")

# -----------------------------
# 2️⃣ Import coinbase_advanced_py from vendor
# -----------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    raise SystemExit(
        "❌ Module coinbase_advanced_py not found. Make sure 'vendor/coinbase_advanced_py' exists."
    )

# -----------------------------
# 3️⃣ Load API keys from environment
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ["true", "1", "yes"]

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
# 4️⃣ Initialize Coinbase client
# -----------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("🚀 Nija Trading Bot initialized (DRY_RUN={} )".format(DRY_RUN))
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -----------------------------
# 5️⃣ Example: check account balances
# -----------------------------
try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# -----------------------------
# 6️⃣ Your bot trading logic continues here
# -----------------------------
if DRY_RUN:
    print("🟡 Running in DRY_RUN mode — no real trades will be executed.")
else:
    # Example placeholder for real trades
    # client.place_order(...)
    print("🟢 Ready to place real trades.")
