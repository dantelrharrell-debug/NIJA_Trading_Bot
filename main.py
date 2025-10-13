#!/usr/bin/env python3
import os
import sys
import traceback
import importlib
from dotenv import load_dotenv

# ----------------- Environment -----------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET in environment variables")

print("✅ API_KEY and API_SECRET loaded")

# ----------------- Debug Installed Packages -----------------
try:
    import pkg_resources
    installed = [p.project_name for p in pkg_resources.working_set]
    print("📦 Installed packages:", installed)
except Exception as e:
    print("⚠️ Could not list installed packages:", e)

# ----------------- Coinbase Client Loader -----------------
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase_advanced_py not installed. Check requirements.txt")

def debug_module_print():
    try:
        attrs = dir(cb)
    except Exception as e:
        attrs = f"Unable to dir() coinbase_advanced_py: {e}"
    print("=== coinbase_advanced_py module debug ===")
    print("module repr:", repr(cb))
    print("module file:", getattr(cb, "__file__", "<no __file>"))
    print("available attributes (dir):")
    print(attrs)
    print("=== end debug ===")

def create_coinbase_client(api_key, api_secret):
    # Attempt standard Client attribute
    if hasattr(cb, "Client"):
        try:
            print("Using cb.Client")
            return cb.Client(api_key, api_secret)
        except Exception as e:
            print("Failed initializing cb.Client:", e)
    
    # Try alternative class names on root module
    for name in ("Client", "CoinbaseClient", "Coinbase", "AdvancedClient"):
        if hasattr(cb, name):
            cls = getattr(cb, name)
            try:
                return cls(api_key, api_secret)
            except Exception as e:
                print(f"Failed initializing {name}: {e}")

    # Try likely submodules
    submodules = ["client", "clients", "api", "core"]
    class_names = ("Client", "client", "CoinbaseClient", "Coinbase")
    for m in submodules:
        try:
            mod = importlib.import_module(f"coinbase_advanced_py.{m}")
            for cname in class_names:
                if hasattr(mod, cname):
                    cls = getattr(mod, cname)
                    try:
                        print(f"Using {cname} from coinbase_advanced_py.{m}")
                        return cls(api_key, api_secret)
                    except Exception as e:
                        print(f"Failed init {cname} from {m}: {e}")
        except Exception:
            pass  # ignore missing submodules

    # Last resort: dump debug info
    debug_module_print()
    raise RuntimeError(
        "Could not find a usable Client class in coinbase_advanced_py."
    )

# ----------------- Initialize Client -----------------
try:
    client = create_coinbase_client(API_KEY, API_SECRET)
    print("✅ Coinbase client created successfully")
except Exception as e:
    print("❌ Failed to create Coinbase client:", e)
    traceback.print_exc()
    sys.exit(1)

# ----------------- Example: Check Balances -----------------
try:
    balances = client.get_account_balances()
    print("✅ Balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# ----------------- TODO: Add trading logic here -----------------
