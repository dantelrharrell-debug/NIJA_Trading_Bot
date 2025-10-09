import sys
import os
import subprocess
import importlib.util

# -----------------------------
# 1️⃣ Function to import or auto-download coinbase_advanced_py
# -----------------------------
def ensure_coinbase_advanced():
    try:
        import coinbase_advanced_py as cb
        print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
        return cb
    except ModuleNotFoundError:
        print("⚠️ coinbase_advanced_py not found. Attempting runtime download...")

    # Setup vendor folder
    VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
    os.makedirs(VENDOR_DIR, exist_ok=True)

    # Download the wheel into vendor
    whl_file = None
    subprocess.check_call([
        sys.executable, "-m", "pip", "download",
        "coinbase-advanced-py==1.8.2",
        "--no-deps", "-d", VENDOR_DIR
    ])

    # Find the .whl file
    for fname in os.listdir(VENDOR_DIR):
        if fname.endswith(".whl") and "coinbase_advanced_py" in fname:
            whl_file = os.path.join(VENDOR_DIR, fname)
            break
    if not whl_file:
        raise SystemExit("❌ Failed to download coinbase_advanced_py wheel.")

    # Unpack wheel into vendor/coinbase_advanced_py
    import zipfile
    with zipfile.ZipFile(whl_file, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(VENDOR_DIR, "coinbase_advanced_py"))

    # Add vendor/coinbase_advanced_py to sys.path
    module_path = os.path.join(VENDOR_DIR, "coinbase_advanced_py")
    if module_path not in sys.path:
        sys.path.insert(0, module_path)

    # Import it again
    import coinbase_advanced_py as cb
    print("✅ Successfully installed and imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
    return cb

# -----------------------------
# 2️⃣ Ensure coinbase_advanced_py is ready
# -----------------------------
cb = ensure_coinbase_advanced()

# -----------------------------
# 3️⃣ Load API keys
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
