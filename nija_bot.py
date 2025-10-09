import sys
import os

# Add vendor folder to sys.path
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print(f"✅ Added vendor folder to sys.path: {VENDOR_DIR}")

# Import vendored coinbase_advanced_py
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    raise SystemExit("❌ Module coinbase_advanced_py not found. Make sure 'vendor/coinbase_advanced_py' exists.")
import sys
import os

# -----------------------------
# 1️⃣ Add pre-vendored folder to sys.path
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
client = cb.Client(API_KEY, API_SECRET)
print("🚀 Nija Trading Bot initialized")

# -----------------------------
# 5️⃣ Your bot logic continues here
# -----------------------------
