#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------
# 1️⃣ Make sure Python can see Render venv
# -----------------------------------------
venv_site = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)
    print("✅ Added Render venv to sys.path:", venv_site)

# -----------------------------------------
# 2️⃣ Load environment variables
# -----------------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# -----------------------------------------
# 3️⃣ Import coinbase_advanced_py
# -----------------------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module 'coinbase_advanced_py' not found:", e)
    raise SystemExit(1)

# -----------------------------------------
# 4️⃣ Initialize client and test fetch
# -----------------------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    balances = client.get_account_balances()
    print("✅ Successfully fetched account balances:")
    for b in balances:
        print(b)
except Exception as e:
    print("❌ Error fetching balances:", e)
