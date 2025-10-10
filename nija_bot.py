#!/usr/bin/env python3
"""
Robust startup for NIJA Trading Bot:
- inspects installed distributions
- finds which top-level package name the coinbase-advanced-py distribution provides
- imports the discovered module and tries to initialize a client
"""
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
print("🚀 Starting Nija Trading Bot (robust importer)")
print("Python:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# Load .env locally if python-dotenv is available (Render will use env vars)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not available or .env missing (expected on Render)")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ API_KEY/API_SECRET not set. Running in DRY_RUN mode only.")
    if not DRY_RUN:
        raise SystemExit("Missing API credentials and DRY_RUN not enabled.")

# ---------- Inspect installed distribution for coinbase-advanced-py ----------
def find_distribution_candidates(dist_name="coinbase-advanced-py"):
    try:
        # Python 3.8+ importlib.metadata
        from importlib import metadata as importlib_metadata
    except Exception:
        try:
            import importlib_metadata as importlib_metadata
        except Exception:
            importlib_metadata = None

    if importlib_metadata is None:
        print("❌ importlib.metadata not available; cannot inspect installed distributions.")
        return []

    try:
        dist = importlib_metadata.distribution(dist_name)
    except importlib_metadata.PackageNotFoundError:
        print(f"❌ Distribution {dist_name} not found via importlib.metadata")
        return []
    except Exception as e:
        print("❌ Error finding distribution:", type(e).__name__, e)
        return []

    print(f"✅ Found distribution: {dist.metadata.get('Name', dist.metadata.get('name','?'))} version {dist.version}")

    file_paths = list(dist.files or [])
    # collect top-level candidates (first path part)
    top_level = []
    for p in file_paths:
        if not p:
            continue
        parts = p.parts
        if len(parts) >= 1:
            top_level.append(parts[0])
    candidates = list(dict.fromkeys(top_level))  # preserve order, unique
    print("Distribution top-level file roots (candidates):", candidates[:40])
    return candidates

candidates = find_distribution_candidates()

# ---------- Try importing likely names if metadata didn't help ----------
COMMON_NAMES = ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase_api", "coinbase_client"]
# merge both lists keeping uniqueness and order
merged_candidates = []
for n in (candidates + COMMON_NAMES):
    if n not in merged_candidates:
        merged_candidates.append(n)

print("Final import attempt order:", merged_candidates[:40])

def try_import(name):
    try:
        mod = __import__(name)
        return mod
    except Exception as e:
        return e

found_mod = None
found_name = None
for name in merged_candidates:
    print(f"Trying import '{name}' ...", end=" ")
    res = try_import(name)
    if isinstance(res, Exception):
        print(f"✖ failed: {type(res).__name__}: {res}")
        continue
    found_mod = res
    found_name = name
    print("✅ OK")
    break

if not found_mod:
    print("❌ Could not import any candidate module for coinbase-advanced-py.")
    print("sys.path sample:", sys.path[:6])
    print("Installed site-packages location (first few):")
    import site
    try:
        print(site.getsitepackages()[:6])
    except Exception:
        print([p for p in sys.path if "site-packages" in p][:6])
    # show pip list snippet for debugging (safe truncation)
    try:
        import subprocess
        out = subprocess.check_output([sys.executable, "-m", "pip", "list"], text=True, stderr=subprocess.STDOUT)
        print("=== pip list (top 60 lines) ===")
        print("\n".join(out.splitlines()[:60]))
    except Exception as e:
        print("Could not run pip list:", e)
    raise SystemExit(1)

print("Imported module name:", found_name)
print("module attributes preview:", [n for n in dir(found_mod) if not n.startswith("_")][:200])

# ---------- Try to find an entrypoint / client within the imported module ----------
Client = None
client_instance = None
client_candidates = ["Client", "client", "AdvancedClient", "CoinbaseClient", "CoinbaseAdvancedClient"]

for attr in client_candidates:
    if hasattr(found_mod, attr):
        Client = getattr(found_mod, attr)
        print(f"✅ Found candidate attribute on module: {attr}")
        break

# Try submodule search (e.g. module.client or module.api)
if Client is None:
    for sub in ("client", "api", "advanced", "sdk"):
        try:
            submod = __import__(f"{found_name}.{sub}", fromlist=["*"])
            if hasattr(submod, "Client"):
                Client = getattr(submod, "Client")
                print(f"✅ Found Client in submodule: {found_name}.{sub}")
                break
        except Exception:
            pass

# If still no Client, try to import package file names from the distribution candidates
if Client is None:
    print("⚠️ No direct 'Client' attribute found on module. Will try to find functional entrypoints.")
    for func_name in ("get_accounts", "get_account_balances", "list_accounts", "accounts"):
        if hasattr(found_mod, func_name):
            print(f"ℹ️ Found function-like entrypoint on module: {func_name}")
            try:
                # try calling with api_key/api_secret (some modules accept kwargs)
                out = getattr(found_mod, func_name)(api_key=API_KEY or "fake", api_secret=API_SECRET or "fake")
                print("Call result (truncated):", str(out)[:400])
            except Exception as e:
                print(f"Call to {func_name} raised {type(e).__name__}: {e}")
            # don't exit — keep searching

# ---------- If we found a Client class, instantiate it ----------
if Client:
    print("Attempting to initialize Client(...)")
    try:
        client_instance = Client(API_KEY or "fake", API_SECRET or "fake")
        print("✅ client instance created:", type(client_instance))
    except TypeError as e:
        print("✖ Client init TypeError:", e)
        # try alternative constructor patterns
        try:
            client_instance = Client(api_key=API_KEY or "fake", api_secret=API_SECRET or "fake")
            print("✅ client instance created via keyword args:", type(client_instance))
        except Exception as e2:
            print("✖ Alternative Client init failed:", type(e2).__name__, e2)
    except Exception as e:
        print("✖ Client initialization failed:", type(e).__name__, e)
        traceback.print_exc()

# ---------- Try a balances/accounts call if available ----------
if client_instance is not None:
    for method in ("get_account_balances", "get_accounts", "accounts", "list_accounts", "get_accounts_sync"):
        if hasattr(client_instance, method):
            try:
                print(f"Calling client.{method}() ...")
                out = getattr(client_instance, method)()
                print("Result:", out)
            except Exception as e:
                print(f"Call raised {type(e).__name__}: {e}")
            break
    else:
        print("⚠️ client instance has no known balance/account method. Attributes:", dir(client_instance)[:80])
else:
    print("⚠️ No client instance was created. Check distribution layout and package internals printed above.")

# ---------- Final: run a short heartbeat so Render log shows activity ----------
print("DRY_RUN =", DRY_RUN, "SANDBOX =", SANDBOX)
try:
    for i in range(6):
        print(f"heartbeat {i+1}/6 — DRY_RUN={DRY_RUN}")
        time.sleep(5)
except KeyboardInterrupt:
    print("Interrupted")
print("🟢 Diagnostic run finished.")
