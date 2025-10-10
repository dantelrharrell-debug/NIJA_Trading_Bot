#!/usr/bin/env python3
import os, sys
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
print("🚀 Starting Nija Trading Bot (diagnostic mode)")
print("Python:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# Try to load .env locally (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not installed or .env missing - that's OK on Render")

# Show pip-installed packages quickly (short list)
try:
    import pkgutil
    tops = [m.name for m in pkgutil.iter_modules()][:60]
    print("Top site packages (first 60):", tops[:30])
except Exception:
    pass

# -------------------
# Try import coinbase_advanced_py
# -------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("❌ ERROR importing coinbase_advanced_py:", type(e).__name__, e)
    print("Hint: ensure coinbase-advanced-py==1.8.2 is in requirements.txt and Render Start Command is 'bash start.sh'")
    print("sys.path sample:", sys.path[:10])
    raise SystemExit(1)

# -------------------
# Read env vars
# -------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1","true","yes")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1","true","yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables.")
    print("Set them in Render → Service → Environment (API_KEY, API_SECRET). Bot will continue only if DRY_RUN=True")
    if not DRY_RUN:
        raise SystemExit(1)

# -------------------
# Initialize client
# -------------------
try:
    # coinbase_advanced_py.Client may accept sandbox kwarg; adapt if your vendored wrapper differs
    client = cb.Client(API_KEY or "fake", API_SECRET or "fake", sandbox=SANDBOX)
    print("🚀 Coinbase client created:", type(client))
except AttributeError:
    print("❌ coinbase_advanced_py doesn't expose 'Client' attribute in this version.")
    print("Check the installed module API or vendored package.")
    raise SystemExit(1)
except Exception as e:
    print("❌ Error when initializing client:", type(e).__name__, e)
    if not DRY_RUN:
        raise SystemExit(1)

# -------------------
# Quick test call (safe)
# -------------------
try:
    if hasattr(client, "get_account_balances"):
        print("Testing get_account_balances() ...")
        balances = client.get_account_balances()
        print("💰 Balances:", balances)
    elif hasattr(client, "get_accounts"):
        print("Testing get_accounts() ...")
        accounts = client.get_accounts()
        print("💰 Accounts:", accounts)
    else:
        print("ℹ️ No account/balance method detected on client. Attributes:", dir(client)[:30])
except Exception as e:
    print("⚠️ Test call failed:", type(e).__name__, e)

# -------------------
# Main loop placeholder
# -------------------
import time
print("✅ Diagnostics complete. Entering placeholder loop (CTRL+C to stop). DRY_RUN =", DRY_RUN)
try:
    while True:
        print("heartbeat — bot alive. DRY_RUN:", DRY_RUN)
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Stopped by user")
