#!/opt/render/project/src/.venv/bin/python3
import sys
import traceback

# 1️⃣ Ensure venv Python is used
print("Python executable:", sys.executable)
print("Python version:", sys.version)

# 2️⃣ Try to import Coinbase Advanced
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully")
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py NOT found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.8.2"])
    import coinbase_advanced_py as cb
    print("✅ Installed and imported coinbase_advanced_py")

# 3️⃣ Initialize sandbox client (replace with real keys later)
API_KEY = "YOUR_SANDBOX_API_KEY"
API_SECRET = "YOUR_SANDBOX_API_SECRET"

try:
    client = cb.Client(API_KEY, API_SECRET, sandbox=True)
    print("✅ Coinbase sandbox client ready")
except Exception:
    print("❌ Failed to initialize client")
    traceback.print_exc()

# 4️⃣ Test a simple call
try:
    accounts = client.list_accounts()
    print("Accounts fetched:", [a['id'] for a in accounts])
except Exception:
    print("❌ Failed to fetch accounts")
    traceback.print_exc()

# 5️⃣ Start the FastAPI/Uvicorn bot
import uvicorn
from main import app  # Make sure your FastAPI app is in main.py

uvicorn.run(app, host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv)>1 else 10000)
