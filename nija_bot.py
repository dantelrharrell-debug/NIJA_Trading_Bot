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

# Try to load .env locally (Render uses env vars in dashboard)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception as e:
    print("ℹ️ python-dotenv not loaded / .env missing:", e)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

print(f"DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX}")
if not API_KEY or not API_SECRET:
    print("⚠️ WARNING: API_KEY or API_SECRET not set. Running in DRY_RUN mode only.")
    if not DRY_RUN:
        raise SystemExit("Missing API keys and DRY_RUN not enabled.")

# ---------- Inspect installed distributions safely ----------
def inspect_installed_distributions():
    try:
        from importlib import metadata as importlib_metadata
    except Exception:
        try:
            import importlib_metadata as importlib_metadata
        except Exception:
            importlib_metadata = None

    if not importlib_metadata:
        print("ℹ️ importlib.metadata not available on this Python; skipping distribution inspection.")
        return

    try:
        names = []
        for d in importlib_metadata.distributions():
            try:
                meta = getattr(d, "metadata", None)
                if meta and hasattr(meta, "get"):
                    name = meta.get("Name") or getattr(d, "name", str(d))
                else:
                    # fallback: Distribution object may provide 'name' attribute
                    name = getattr(d, "name", str(d))
            except Exception:
                name = getattr(d, "name", str(d))
            names.append(name)
        print("Sample installed distributions (first 80):", names[:80])
    except Exception as e:
        print("Error while enumerating distributions:", type(e).__name__, e)

def list_site_packages_for_coinbase():
    import site
    candidates = []
    try:
        candidates = site.getsitepackages()
    except Exception:
        candidates = [p for p in sys.path if "site-packages" in p]
    print("site-packages candidates:", candidates[:6])
    for sp in candidates:
        try:
            p = Path(sp)
            if p.exists():
                found = sorted([x.name for x in p.glob("coinbase*")])[:200]
                if found:
                    print(f"Found coinbase* items in {sp}: {found[:60]}")
        except Exception:
            pass

print("=== Inspecting installed distributions and site-packages for coinbase package files ===")
inspect_installed_distributions()
list_site_packages_for_coinbase()

# ---------- Try multiple import names ----------
def try_import_names():
    candidates = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase",
    ]
    for name in candidates:
        try:
            print(f"Trying import '{name}' ...")
            mod = __import__(name)
            print(f"✅ Imported module '{name}' as {getattr(mod,'__name__',str(mod))}")
            return mod
        except Exception as e:
            print(f"  ✖ failed import '{name}': {type(e).__name__}: {e}")
    return None

mod = try_import_names()
if not mod:
    print("❌ Module not importable under common names.")
    print("Ensure: (1) requirements.txt contains 'coinbase-advanced-py==1.8.2' AND (2) Render Start Command is 'bash start.sh'")
    try:
        import subprocess
        out = subprocess.check_output([sys.executable, "-m", "pip", "list"], stderr=subprocess.STDOUT, text=True)
        print("=== pip list (truncated) ===")
        print("\n".join(out.splitlines()[:80]))
    except Exception as e:
        print("Could not run pip list:", e)
    raise SystemExit(1)

# ---------- Inspect module and try to find a client ----------
print("module dir preview:", [n for n in dir(mod) if not n.startswith("_")][:200])

Client = None
for candidate in ("Client", "client", "AdvancedClient", "CoinbaseClient"):
    if hasattr(mod, candidate):
        Client = getattr(mod, candidate)
        print(f"✅ Found client-like attribute on module: {candidate}")
        break

# try submodule client
if Client is None:
    try:
        sub = __import__(f"{mod.__name__}.client", fromlist=["Client"])
        if hasattr(sub, "Client"):
            Client = getattr(sub, "Client")
            print("✅ Found Client in submodule '.client'")
    except Exception:
        pass

api_key = API_KEY or "fake"
api_secret = API_SECRET or "fake"

client = None
try:
    if Client:
        client = Client(api_key, api_secret)
        print("✅ Initialized client object:", type(client))
    else:
        # Try function-style entrypoints
        if hasattr(mod, "get_accounts"):
            print("ℹ️ Using mod.get_accounts(...) as fallback")
            accounts = mod.get_accounts(api_key=api_key, api_secret=api_secret)
            print("Accounts:", accounts)
        elif hasattr(mod, "get_accounts_sync"):
            accounts = mod.get_accounts_sync(api_key=api_key, api_secret=api_secret)
            print("Accounts (sync):", accounts)
        else:
            print("⚠️ No obvious initializer found on package. Attributes:", dir(mod)[:120])
except Exception as e:
    print("❌ Error while attempting to initialize client:", type(e).__name__, e)
    traceback.print_exc()
    if not DRY_RUN:
        raise SystemExit(1)

# attempt a balances/accounts call if client exists
if client is not None:
    try:
        if hasattr(client, "get_account_balances"):
            balances = client.get_account_balances()
            print("💰 Account balances:", balances)
        elif hasattr(client, "get_accounts"):
            accounts = client.get_accounts()
            print("💰 Accounts:", accounts)
        else:
            print("ℹ️ Client has no get_account_balances/get_accounts. Sample attrs:", dir(client)[:80])
    except Exception as e:
        print("❌ Error calling client methods:", type(e).__name__, e)

if DRY_RUN:
    print("✅ DRY_RUN mode — no live orders will be placed.")
else:
    print("⚠️ Live mode: your bot may place orders — be careful!")

# small heartbeat so logs show activity (short)
import time
try:
    for i in range(6):
        print(f"💓 heartbeat {i+1}/6 — DRY_RUN={DRY_RUN}")
        time.sleep(5)
except KeyboardInterrupt:
    print("🛑 Interrupted")
print("🟢 Diagnostic run completed.")
