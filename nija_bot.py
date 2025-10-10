#!/usr/bin/env python3
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
print("🚀 Starting Nija Trading Bot (diagnostic mode)")
print("Python executable:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception as e:
    print("ℹ️ python-dotenv not loaded:", e)

# read env keys (Render: set these in service's Environment)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1","true","yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1","true","yes")

print(f"DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX}")
if not API_KEY or not API_SECRET:
    print("⚠️ WARNING: API_KEY or API_SECRET not set. Running in DRY_RUN mode only.")
    if not DRY_RUN:
        raise SystemExit("Missing API keys and DRY_RUN not enabled.")

# Helper: inspect site-packages for coinbase stuff
def list_site_packages():
    import site
    sps = []
    try:
        sps = site.getsitepackages()
    except Exception:
        # fallback
        sps = [p for p in sys.path if "site-packages" in p]
    print("site-packages candidates:", sps[:6])
    for sp in sps:
        try:
            p = Path(sp)
            if p.exists():
                items = sorted([x.name for x in p.glob("coinbase*")][:200])
                if items:
                    print(f"Found in {sp}: {items[:60]}")
        except Exception:
            pass

# Try to import the package using several known names
def try_import_names():
    names = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase_advanced_py-1.8.2",  # nonsense but harmless
        "coinbase_advanced_py.__init__",
        "coinbase",  # sometimes upstream packages use coinbase top-level
    ]
    for name in names:
        try:
            print(f"Trying import '{name}' ...")
            mod = __import__(name)
            print(f"✅ Imported module named '{name}' -> {getattr(mod, '__name__', str(mod))}")
            return mod
        except Exception as e:
            print(f"  ✖ failed: {type(e).__name__}: {e}")
    return None

# Attempt import via importlib.metadata to check distributions
def inspect_installed_distributions():
    try:
        from importlib import metadata
    except Exception:
        try:
            import importlib_metadata as metadata
        except Exception:
            metadata = None

    if metadata:
        dists = []
        try:
            dists = [d for d in metadata.distributions()]
        except Exception:
            try:
                dists = metadata.distributions()
            except Exception:
                dists = []
        names = [getattr(d, "metadata", lambda: {})().get("Name", str(d)) for d in list(dists)[:200]]
        print("Top installed distributions sample (first 80):", names[:80])
        # try metadata for coinbase-advanced-py specifically
        try:
            info = metadata.metadata("coinbase-advanced-py")
            print("metadata for coinbase-advanced-py:", dict(info))
        except Exception as e:
            print("No metadata for coinbase-advanced-py found via importlib.metadata:", type(e).__name__, e)

print("=== Inspecting installed distributions and site-packages for coinbase package files ===")
inspect_installed_distributions()
list_site_packages()

print("=== Trying to import coinbase module variants ===")
mod = try_import_names()
if not mod:
    print("❌ Module 'coinbase_advanced_py' not importable under common names.")
    print("Please confirm: (1) requirements.txt contains 'coinbase-advanced-py==1.8.2' AND (2) start command is 'bash start.sh' so pip runs in the same environment.")
    # show pip list for logging if possible
    try:
        import subprocess
        out = subprocess.check_output([sys.executable, "-m", "pip", "list"], stderr=subprocess.STDOUT, text=True)
        print("=== pip list (truncated) ===")
        print("\n".join(out.splitlines()[:80]))
    except Exception as e:
        print("Could not run pip list:", e)
    raise SystemExit(1)

# If we got a module, try to find a client class or factory in the module
print("✅ Module import succeeded. Inspecting module attributes:", getattr(mod, "__name__", None))
print("module dir preview:", [n for n in dir(mod) if not n.startswith("_")][:120])

# Try common client entry points:
Client = None
for candidate in ("Client", "client", "CoinbaseClient", "AdvancedClient"):
    if hasattr(mod, candidate):
        Client = getattr(mod, candidate)
        print(f"✅ Found client attribute on module: {candidate}")
        break

# If module is a package with submodules, try recommended import path
if Client is None:
    try:
        sub = None
        # try from coinbase_advanced_py.client import Client
        try:
            sub = __import__(f"{mod.__name__}.client", fromlist=["Client"])
            if hasattr(sub, "Client"):
                Client = getattr(sub, "Client")
                print("✅ Found Client in submodule '.client'")
        except Exception:
            pass
    except Exception:
        pass

if Client is None:
    print("⚠️ No Client class found automatically. The package may expose functions instead.")
    # we'll attempt to proceed with function-based usages if available later

# Safe initialization: use DRY_RUN default credentials if not set
api_key = API_KEY or "fake"
api_secret = API_SECRET or "fake"

# Try to initialize client or call top-level helper functions
try:
    if Client:
        client = Client(api_key, api_secret)
        print("✅ Initialized client object:", type(client))
    else:
        # try top-level function names
        if hasattr(mod, "Client"):
            client = mod.Client(api_key, api_secret)
            print("✅ Initialized client via mod.Client")
        elif hasattr(mod, "get_accounts"):
            print("ℹ️ package provides get_accounts function; calling it (DRY_RUN safe)...")
            accounts = mod.get_accounts(api_key=api_key, api_secret=api_secret)
            print("Accounts:", accounts)
            client = None
        elif hasattr(mod, "get_accounts_sync"):
            accounts = mod.get_accounts_sync(api_key=api_key, api_secret=api_secret)
            print("Accounts (sync):", accounts)
            client = None
        else:
            print("⚠️ No obvious initialization API found on module. Here are attributes:", dir(mod)[:200])
            client = None
except Exception as e:
    print("❌ Error while attempting to initialize client:", type(e).__name__, e)
    traceback.print_exc()
    if not DRY_RUN:
        raise SystemExit(1)

# If we have a client object, try to call typical balance methods
if 'client' in locals() and client is not None:
    try:
        if hasattr(client, "get_account_balances"):
            balances = client.get_account_balances()
            print("💰 Account balances:", balances)
        elif hasattr(client, "get_accounts"):
            accounts = client.get_accounts()
            print("💰 Accounts:", accounts)
        else:
            print("ℹ️ Client object does not provide get_account_balances/get_accounts. Attributes:", dir(client)[:120])
    except Exception as e:
        print("❌ Error fetching balances/accounts:", type(e).__name__, e)

# If everything above succeeded, continue to main trading loop (placeholder)
if DRY_RUN:
    print("✅ DRY_RUN mode — no live orders will be placed. Replace with real logic.")
else:
    print("⚠️ Live mode: your bot may place orders. Ensure credentials are correct!")

# Example small heartbeat loop so Render logs show bot is alive
import time
try:
    for i in range(6):  # print 6 heartbeats then exit (prevents runaway in tests)
        print(f"💓 heartbeat {i+1}/6 — DRY_RUN={DRY_RUN}")
        time.sleep(5)
except KeyboardInterrupt:
    print("🛑 Interrupted by user")
print("🟢 Diagnostic run completed.")
