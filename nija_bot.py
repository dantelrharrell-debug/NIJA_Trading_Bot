# nija_bot.py

# -----------------------------
# 1️⃣ Imports & setup
# -----------------------------
from coinbase.rest import RESTClient
import os

# -----------------------------
# 2️⃣ Load API keys
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# -----------------------------
# 3️⃣ DRY_RUN flag for testing
# -----------------------------
DRY_RUN = True  # Set True until your PEM/API key works

# -----------------------------
# 4️⃣ Instantiate client
# -----------------------------
client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)

if DRY_RUN:
    print("✅ DRY_RUN: Client instantiated successfully (no API calls executed)")

if not DRY_RUN:
    accounts = client.get_accounts()
    print(accounts)

#!/usr/bin/env python3
"""
Robust nija_bot startup script.

- Tries to import coinbase-ish packages installed by pip.
- Scans the package for submodules and classes named *Client or factory functions.
- Instantiates a client if possible (DRY_RUN safe).
- If no client found, prints diagnostics to help decide the next step.
"""
import sys
import os
import pkgutil
import importlib
import inspect
import traceback
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
print("🚀 Starting Nija Trading Bot (robust importer)")
print("Python:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# Show coinbase-ish modules visible to this interpreter
found = []
for m in pkgutil.iter_modules():
    if m.name.startswith("coinbase"):
        found.append(m.name)
print("coinbase-ish modules found:", found)

# Candidate names (order matters)
CANDIDATES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_api",
    "coinbase_client",
    "coinbase",  # fallback
]

module = None
mod_name = None
for name in CANDIDATES:
    try:
        module = importlib.import_module(name)
        mod_name = name
        print(f"✅ Imported module: {name} (file={getattr(module,'__file__',None)})")
        break
    except Exception as e:
        print(f"✖ Import {name} failed: {type(e).__name__}: {e}")

if module is None:
    print("❌ Could not import any coinbase* module. Ensure requirements.txt includes coinbase-advanced-py==1.8.2 and start.sh installs it.")
    raise SystemExit(1)

# Print top-level attributes (non-private)
attrs = [a for a in dir(module) if not a.startswith("_")]
print("Top-level attributes on imported module:", attrs[:120])

# If module has __path__, list top-level submodules
if hasattr(module, "__path__"):
    print("Submodules inside package:")
    for sub in pkgutil.iter_modules(module.__path__):
        print(" -", sub.name)

# Helper: find classes named *Client in module and submodules
ClientClass = None
factory_fn = None

def find_client_class_in_obj(obj):
    # return first class where name endswith 'Client'
    for name, val in inspect.getmembers(obj, inspect.isclass):
        if name.lower().endswith("client"):
            return val, f"{obj.__name__}.{name}" if hasattr(obj, "__name__") else name
    return None, None

# 1) check module itself
c, where = find_client_class_in_obj(module)
if c:
    ClientClass = c
    print(f"ℹ️ Found ClientClass at {where}")

# 2) check common submodules
if ClientClass is None and hasattr(module, "__path__"):
    for sub in pkgutil.iter_modules(module.__path__):
        try:
            submod = importlib.import_module(f"{mod_name}.{sub.name}")
            c, where = find_client_class_in_obj(submod)
            if c:
                ClientClass = c
                print(f"ℹ️ Found ClientClass at {mod_name}.{sub.name}.{c.__name__}")
                break
        except Exception:
            pass

# 3) check for factory functions on module: create_client, get_client, client_from_env, Client (callable)
for fn in ("create_client", "get_client", "client_from_env", "create_client_from_env", "Client"):
    if hasattr(module, fn) and callable(getattr(module, fn)):
        factory_fn = getattr(module, fn)
        print(f"ℹ️ Found factory function on module: {fn}")
        break

# 4) check submodules for factory functions
if factory_fn is None and hasattr(module, "__path__"):
    for sub in pkgutil.iter_modules(module.__path__):
        try:
            submod = importlib.import_module(f"{mod_name}.{sub.name}")
            for fn in ("create_client", "get_client", "client_from_env", "create_client_from_env", "Client"):
                if hasattr(submod, fn) and callable(getattr(submod, fn)):
                    factory_fn = getattr(submod, fn)
                    print(f"ℹ️ Found factory function at {mod_name}.{sub.name}.{fn}")
                    break
            if factory_fn:
                break
        except Exception:
            pass

# 5) as a last resort search all attributes for callables with 'client' in name
if ClientClass is None and factory_fn is None:
    for name in attrs:
        try:
            val = getattr(module, name)
            if callable(val) and "client" in name.lower() and name.lower() != "client":
                factory_fn = val
                print(f"ℹ️ Found client-like callable: {name} on module")
                break
        except Exception:
            pass

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not available or .env missing (OK on Render).")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes", "y", "1")

if not API_KEY or not API_SECRET:
    print("⚠️ API_KEY or API_SECRET not set in env. Bot will run in DRY_RUN mode.")
    if not DRY_RUN:
        print("❌ DRY_RUN is False but credentials missing — aborting.")
        raise SystemExit(1)

# Instantiate client
client = None
if ClientClass is not None:
    try:
        # try common constructor signatures
        try:
            client = ClientClass(API_KEY, API_SECRET)
        except TypeError:
            try:
                client = ClientClass(api_key=API_KEY, api_secret=API_SECRET)
            except Exception:
                client = ClientClass()
        print("🚀 Instantiated client from ClientClass:", type(client))
    except Exception as e:
        print("❌ ClientClass instantiation failed:", type(e).__name__, e)
        traceback.print_exc()
elif factory_fn is not None:
    try:
        # try calling factory function
        try:
            client = factory_fn(API_KEY, API_SECRET)
        except TypeError:
            try:
                client = factory_fn(api_key=API_KEY, api_secret=API_SECRET)
            except TypeError:
                client = factory_fn()
        print("🚀 Client produced by factory function:", type(client))
    except Exception as e:
        print("❌ Factory function invocation failed:", type(e).__name__, e)
        traceback.print_exc()
else:
    print("⚠️ No Client class or factory found. Will try to call direct API functions if present.")

# Try a safe accounts/balances check
def safe_accounts_check():
    try:
        # client methods
        if client is not None:
            for name in ("get_account_balances", "get_accounts", "list_accounts", "accounts"):
                if hasattr(client, name) and callable(getattr(client, name)):
                    print("💰 Calling client.", name)
                    res = getattr(client, name)()
                    print("Accounts result:", res)
                    return True

        # module-level functions
        for name in ("get_account_balances", "get_accounts", "list_accounts"):
            if hasattr(module, name) and callable(getattr(module, name)):
                fn = getattr(module, name)
                print("💰 Calling module function", name)
                try:
                    res = fn(API_KEY, API_SECRET) if API_KEY else fn()
                except TypeError:
                    res = fn()
                print("Accounts result:", res)
                return True
    except Exception as e:
        print("ℹ️ accounts check failed:", type(e).__name__, e)
        traceback.print_exc()
    return False

if safe_accounts_check():
    print("✅ Accounts check succeeded (no trades executed).")
else:
    print("⚠️ Accounts check did not succeed. The installed package layout may require a specific import path or usage.")
    print("Module file:", getattr(module, "__file__", None))
    print("Module repr:", module)
    print("Top-level attributes again:", attrs[:200])

    # Show submodule files (if possible) to aide debugging
    if hasattr(module, "__path__"):
        print("\n--- Listing package files for debugging ---")
        for pkgpath in module.__path__:
            try:
                import os
                for root, dirs, files in os.walk(pkgpath):
                    print("PATH:", root)
                    for f in files[:200]:
                        print("  ", f)
                    break
            except Exception as e:
                print("Could not list package path:", e)

    # Print safe instructions to add to your message for next step
    print("\nNEXT STEPS (copy & paste these two lines into chat if you want me to finish):")
    print("1) The top 30 attrs printed above (copy them).")
    print("2) The first PATH printed in 'Module file:' above (copy that path).")
    print("With those I will tell you the exact import to use.")

# Minimal safe heartbeat loop (so Render shows activity)
print("DRY_RUN =", DRY_RUN)
import time
try:
    for i in range(3):
        print(f"♥ heartbeat {i+1}/3 — DRY_RUN={DRY_RUN}")
        time.sleep(1)
    print("✅ Startup diagnostics finished.")
except KeyboardInterrupt:
    print("🛑 stopped by user")
