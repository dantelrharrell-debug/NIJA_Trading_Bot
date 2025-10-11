#!/usr/bin/env python3
"""
Robust Coinbase REST client instantiation for Render.

Behavior:
- Reads API_KEY, API_SECRET, API_PEM from environment.
- Tries multiple ways to create the REST client:
    - pass private_key (PEM string)
    - pass private_key_path (temp file path)
    - try positional arguments
    - introspect RESTClient signature for supported kwargs
- Provides clear log statements for Render live tail.
"""

import os
import sys
import tempfile
import inspect
import traceback

print("🚀 Starting nija_bot (robust client instantiation)")
print("Python executable:", sys.executable)
print("Working dir:", os.getcwd())
print("sys.path head:", sys.path[:3])

# load env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")  # full PEM value (BEGIN/END lines)
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ WARNING: API_KEY or API_SECRET missing from environment.")
    if not DRY_RUN:
        raise SystemExit("Missing API credentials and not in DRY_RUN.")

# try import the package and locate an appropriate client class
client = None
instantiation_error = None

try:
    # The package installs top-level module 'coinbase' with submodule rest
    import coinbase
    print("✅ Imported top-level module 'coinbase' (file):", getattr(coinbase, "__file__", "unknown"))
except Exception as e:
    print("❌ Failed to import top-level 'coinbase':", type(e).__name__, e)
    traceback.print_exc()
    raise SystemExit(1)

# find RESTClient (most likely location)
RESTClient = None
candidates = [
    ("coinbase.rest", "RESTClient"),
    ("coinbase", "RESTClient"),
    ("coinbase_client", "RESTClient"),
    ("coinbase_advanced", "RESTClient"),
    ("coinbase_advanced_py", "RESTClient"),
]

for mod_name, class_name in candidates:
    try:
        mod = __import__(mod_name, fromlist=[class_name])
        if hasattr(mod, class_name):
            RESTClient = getattr(mod, class_name)
            print(f"✅ Found RESTClient at {mod_name}.{class_name}")
            break
    except Exception:
        # ignore import errors; continue searching
        pass

if RESTClient is None:
    # try introspecting coinbase package for submodules
    try:
        import pkgutil
        for finder, name, ispkg in pkgutil.iter_modules(coinbase.__path__):
            try:
                m = __import__(f"coinbase.{name}", fromlist=["*"])
                if hasattr(m, "RESTClient"):
                    RESTClient = getattr(m, "RESTClient")
                    print(f"✅ Found RESTClient at coinbase.{name}.RESTClient")
                    break
            except Exception:
                pass
    except Exception:
        pass

if RESTClient is None:
    print("❌ Could not find RESTClient class in coinbase package. Aborting.")
    raise SystemExit(1)

# Show signature for diagnostics
try:
    sig = inspect.signature(RESTClient)
    print("RESTClient signature:", sig)
except Exception:
    print("Could not get signature for RESTClient.")

# Helper: try to instantiate with kwargs, catch TypeError
def try_instantiate(**kwargs):
    global client, instantiation_error
    try:
        c = RESTClient(**kwargs)
        print("✅ Client instantiated with kwargs:", list(kwargs.keys()))
        client = c
        return True
    except TypeError as e:
        instantiation_error = e
        print("❌ TypeError with kwargs", kwargs.keys(), ":", e)
        return False
    except Exception as e:
        instantiation_error = e
        print("❌ Other error while instantiating client with", kwargs.keys(), ":", type(e).__name__, e)
        traceback.print_exc()
        return False

# Try approaches in order
# 1) If API_PEM present, try passing as private_key (string)
if API_PEM:
    print("🔐 API_PEM found in environment; trying to use PEM string")
    # try passing private_key directly
    if try_instantiate(api_key=API_KEY, api_secret=API_SECRET, private_key=API_PEM):
        pass
    else:
        # 2) try writing to temp file and pass a few possible kw names
        try:
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
            tf.write(API_PEM.encode("utf-8"))
            tf.flush()
            tf.close()
            pem_path = tf.name
            print("✅ Wrote API_PEM to temporary file:", pem_path)
        except Exception as e:
            print("❌ Failed to write PEM to temp file:", e)
            pem_path = None

        if pem_path:
            for kw in ("private_key_path", "private_key_file", "private_keyfile", "keyfile", "pem_path"):
                if try_instantiate(api_key=API_KEY, api_secret=API_SECRET, **{kw: pem_path}):
                    break

# 3) Try common kw names without PEM (some implementations take key id/secret and look up files)
if client is None:
    print("🔁 Trying other common constructor patterns")
    # try typical names
    for kwargs in [
        {"api_key": API_KEY, "api_secret": API_SECRET},
        {"key": API_KEY, "secret": API_SECRET},
        {"api_key": API_KEY, "secret": API_SECRET},
        {"api_key": API_KEY, "api_secret": API_SECRET, "sandbox": True},
    ]:
        if try_instantiate(**kwargs):
            break

# 4) Try positional instantiation fallbacks (some clients accept (api_key, api_secret, private_key))
if client is None:
    print("🔁 Trying positional instantiation fallback")
    try:
        if API_PEM:
            c = RESTClient(API_KEY, API_SECRET, API_PEM)
        else:
            c = RESTClient(API_KEY, API_SECRET)
        client = c
        print("✅ Client instantiated using positional args")
    except Exception as e:
        instantiation_error = e
        print("❌ Positional instantiation failed:", type(e).__name__, e)
        traceback.print_exc()

# Final check
if client is None:
    print("\n❌ ALL attempts to instantiate RESTClient failed.")
    print("Last error:", type(instantiation_error).__name__, instantiation_error)
    print("Review Render env variables: API_KEY, API_SECRET, API_PEM.")
    raise SystemExit(1)

# If we got a client — print a light account check (safe)
print("✅ REST client ready:", client.__class__)

try:
    # prefer safe read-only method names; adapt depending on package
    if hasattr(client, "get_account_balances"):
        print("ℹ️ Calling get_account_balances() (read-only)")
        print(client.get_account_balances())
    elif hasattr(client, "get_accounts"):
        print("ℹ️ Calling get_accounts() (read-only)")
        print(client.get_accounts())
    elif hasattr(client, "get"):
        print("ℹ️ Client has generic 'get' method; attempting /accounts")
        print(client.get("/accounts"))
    else:
        print("ℹ️ No known read method found on client; skipping account check.")
except Exception as e:
    print("⚠️ Account/read check failed (this may be due to key permissions or PEM format):", type(e).__name__, e)
    # don't crash if DRY_RUN
    if not DRY_RUN:
        print("Exiting because not in DRY_RUN.")
        raise SystemExit(1)

# ---------- Main bot loop (placeholder) ----------
import time
print("✅ Startup complete. Entering heartbeat loop (DRY_RUN=%s)" % DRY_RUN)
try:
    while True:
        print("Heartbeat - bot alive. DRY_RUN=%s" % DRY_RUN)
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Stopped by user")
