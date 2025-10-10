#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Ensure Python sees packages in Render's virtualenv
venv_site = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)
    print("✅ Added Render venv to sys.path:", venv_site)

# Try importing the module
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module 'coinbase_advanced_py' not found:", e)
    raise SystemExit(1)
#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import coinbase_advanced_py as cb

# Load .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize client
client = cb.Client(API_KEY, API_SECRET)

# Example fetch accounts
balances = client.get_account_balances()
print(balances)
