#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

print("🚀 Starting Nija Trading Bot (Option B - install from PyPI)")
print("Python:", sys.executable)
print("sys.path head:", sys.path[:4])

# -----------------------------
# 0) Optional: load .env for local testing (Render uses environment vars in dashboard)
# -----------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env (if present)")
except Exception:
    # dotenv is optional; we still continue
    pass

# -----------------------------
# 1) Import coinbase package installed by pip
# -----------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("❌ Failed to import coinbase_advanced_py:", type(e).__name__, e)
    print("Make sure requirements.txt contains: coinbase-advanced-py==1.8.2 and start.sh runs pip install -r requirements.txt")
    print("sys.path (head):", sys.path[:8])
    raise SystemExit(1)

# -----------------------------
# 2) Read required environment variables (set these in Render dashboard)
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables. Set them in Render dashboard or .env for local testing.")
    # For safety, abort here (remove if you want to run dry without keys)
    # raise SystemExit("Missing API keys")

# -----------------------------
# 3) Instantiate client (guard attribute errors)
# -----------------------------
try:
    client = cb.Client(API_KEY or "fake", API_SECRET or "fake", sandbox=SANDBOX)
    print("🚀 Coinbase client created:", type(client))
except AttributeError:
    print("❌ coinbase_advanced_py has no attribute 'Client' — package structure may differ.")
    raise SystemExit(1)
except Exception as e:
    print("❌ Error creating client:", type(e).__name__, e)
    # don't die here if you want to run in DRY_RUN
    if not DRY_RUN:
        raise SystemExit(1)

# -----------------------------
# 4) Try a harmless call (non-destructive)
# -----------------------------
try:
    # some versions provide get_account_balances, get_accounts, or similar — try common names
    if hasattr(client, "get_account_balances"):
        balances = client.get_account_balances()
        print("💰 Balances:", balances)
    elif hasattr(client, "get_accounts"):
        accounts = client.get_accounts()
        print("💰 Accounts:", accounts)
    else:
        print("ℹ️ Client does not expose a standard balance method. Inspect client: ", dir(client)[:50])
except Exception as e:
    print("ℹ️ Could not fetch balances (maybe sandbox/credentials):", type(e).__name__, e)

# -----------------------------
# 5) Your bot logic starts here (placeholder)
# -----------------------------
try:
    # Placeholder loop; replace with your trading logic
    import time
    while True:
        print("Tick — bot running (DRY_RUN=%s, SANDBOX=%s)" % (DRY_RUN, SANDBOX))
        time.sleep(30)
except KeyboardInterrupt:
    print("Stopped by user")
