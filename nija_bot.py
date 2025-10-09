import sys
import os

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

import coinbase_advanced_py as cb
print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))import sys
import os

# -----------------------------
# 1️⃣ Add vendor folder to sys.path
# -----------------------------
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print(f"✅ Added vendor folder to sys.path: {VENDOR_DIR}")

# -----------------------------
# 2️⃣ Import vendored coinbase_advanced_py
# -----------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    raise SystemExit("❌ Module coinbase_advanced_py not found. Make sure 'vendor/coinbase_advanced_py' exists.")

# -----------------------------
# 3️⃣ Load API keys from environment
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
# 4️⃣ Initialize Coinbase client
# -----------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("🚀 Nija Trading Bot initialized")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -----------------------------
# 5️⃣ Example: fetch account balances
# -----------------------------
try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# -----------------------------
# 6️⃣ Your bot logic continues here
# -----------------------------
# Example placeholder:
# client.place_order(...)
