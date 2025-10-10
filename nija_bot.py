#!/usr/bin/env python3
# nija_bot.py - robust importer for coinbase-advanced-py and safe startup

import sys
import os
import pkgutil
import importlib
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
print("🚀 Starting Nija Trading Bot (diagnostic mode)")
print("Python:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# Show coinbase-ish modules visible to this interpreter (helpful in logs)
coinbase_candidates = [m.name for m in pkgutil.iter_modules() if m.name.startswith("coinbase")]
print("coinbase-ish modules found:", coinbase_candidates)

# try import many likely module names (order matters)
TRY_NAMES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_api",
    "coinbase_client",
    "coinbase",  # fallback that some installers expose
]

cb = None
cb_name = None
for name in TRY_NAMES:
    try:
        cb = importlib.import_module(name)
        cb_name = name
        print(f"✅ Imported {name}")
        break
    except Exception as e:
        print(f"✖ could not import {name}: {type(e).__name__}: {e}")

if cb is None:
    print("❌ Could not import any coinbase-* module. Ensure requirements.txt contains coinbase-advanced-py==1.8.2 and Render ran start.sh.")
    raise SystemExit(1)

# Inspect module attributes to find an entrypoint
print("ℹ️ Inspecting module attributes:", sorted([a for a in dir(cb) if not a.startswith("_")])[:60])

# Common patterns:
# - a Client class: cb.Client or cb.client.Client or cb.client.ClientClass
# - factory function: cb.get_accounts(api_key=..., api_secret=...)
# We'll try to find a Client class first, then common factory functions.

ClientClass = None
factory_fn = None

# 1) direct attribute Client
if hasattr(cb, "Client"):
    ClientClass = getattr(cb, "Client")
    print("ℹ️ Found Client on module:", ClientClass)
else:
    # 2) some packages put client under submodule 'client' or 'api' — try common locations
    for sub in ("client", "api", "client_api"):
        try:
            submod = importlib.import_module(f"{cb_name}.{sub}")
            if hasattr(submod, "Client"):
                ClientClass = getattr(submod, "Client")
                print(f"ℹ️ Found Client in submodule {cb_name}.{sub}")
                break
        except Exception:
            pass

# 3) factory function names
for fn in ("create_client", "get_client", "Client", "client", "create_client_from_env"):
    if hasattr(cb, fn) and callable(getattr(cb, fn)):
        factory_fn = getattr(cb, fn)
        print(f"ℹ️ Found factory function {fn} on module")
        break

# 4) fallback: some releases expose convenience functions like get_accounts directly
if factory_fn is None and ClientClass is None:
    for fn in ("get_accounts", "get_account_balances", "list_accounts"):
        if hasattr(cb, fn) and callable(getattr(cb, fn)):
            factory_fn = getattr(cb, fn)
            print(f"ℹ️ Found top-level API function {fn} (we'll call it directly later).")
            break

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not available or .env missing (OK on Render).")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables! Set them in Render Service → Environment.")
    if not DRY_RUN:
        raise SystemExit("Missing credentials and DRY_RUN is False. Aborting.")
    print("⚠️ Running in DRY_RUN (no trades).")

# Create client or use factory
client = None
if ClientClass is not None:
    try:
        client = ClientClass(API_KEY or "fake", API_SECRET or "fake")
        print("🚀 ClientClass instantiated:", type(client))
    except Exception as e:
        print("❌ Failed to instantiate ClientClass:", type(e).__name__, e)
elif factory_fn is not None:
    try:
        # some factory functions want (api_key, api_secret) or kwargs
        try:
            client = factory_fn(API_KEY, API_SECRET)
        except TypeError:
            client = factory_fn(api_key=API_KEY, api_secret=API_SECRET)
        print("🚀 Client created via factory function:", type(client))
    except Exception as e:
        print("❌ Factory function failed:", type(e).__name__, e)
else:
    print("⚠️ No Client or factory found; falling back to direct API function calls if present.")

# Quick smoke test: find account listing function on client or module
def try_accounts():
    try:
        if client is not None:
            # try common methods
            for fname in ("get_account_balances", "get_accounts", "list_accounts", "accounts"):
                if hasattr(client, fname) and callable(getattr(client, fname)):
                    res = getattr(client, fname)()
                    print("💰 Accounts from client.", fname, "=>", res)
                    return True
        # try module-level functions
        for fname in ("get_account_balances", "get_accounts", "list_accounts"):
            if hasattr(cb, fname) and callable(getattr(cb, fname)):
                res = getattr(cb, fname)(API_KEY, API_SECRET) if API_KEY else getattr(cb, fname)()
                print("💰 Accounts from module.", fname, "=>", res)
                return True
    except Exception as e:
        print("ℹ️ accounts check failed:", type(e).__name__, e)
    return False

if try_accounts():
    print("✅ Accounts check succeeded (no trades executed).")
else:
    print("⚠️ Accounts check did not succeed; the module layout is unusual. You may need to check the package internals.")
    # Show more info to debug
    print("Module file:", getattr(cb, "__file__", "unknown"))
    print("Module repr:", cb)

# -----------------------------
# Main bot loop placeholder (safe)
# -----------------------------
if DRY_RUN:
    print("ℹ️ DRY_RUN mode: bot will not place trades. Set DRY_RUN env to False to allow live trading.")

import time
try:
    for i in range(3):  # small heartbeat loop so Render logs show the bot working
        print(f"❤️ heartbeat {i+1}/3 — DRY_RUN={DRY_RUN}")
        time.sleep(1)
    print("✅ Startup complete. Replace the placeholder loop below with real trading logic.")
except KeyboardInterrupt:
    print("🛑 Stopped by user")
