import sys
print("Python path:", sys.path)
import pip
print("Installed packages:", pip.get_installed_distributions())

# main.py (top portion) - paste/replace this block at the top of your file

#!/usr/bin/env python3
import os
import importlib
import traceback
import sys
import json
import coinbase_advanced_py as cb

# ---------- robust client loader for coinbase_advanced_py ----------
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
    # 1) Try the expected export
    try:
        if hasattr(cb, "Client"):
            print("Using coinbase_advanced_py.Client")
            return cb.Client(api_key, api_secret)
        if hasattr(cb, "client") and hasattr(cb.client, "Client"):
            print("Using coinbase_advanced_py.client.Client")
            return cb.client.Client(api_key, api_secret)
    except Exception as e:
        print("Attempt using cb.Client failed:", e)
        traceback.print_exc()

    # 2) Try common alternative class names on root module
    for name in ("Client", "CoinbaseClient", "Coinbase", "AdvancedClient"):
        if hasattr(cb, name):
            cls = getattr(cb, name)
            try:
                print(f"Trying {name} from root module")
                return cls(api_key, api_secret)
            except TypeError:
                try:
                    return cls(api_key=api_key, api_secret=api_secret)
                except Exception as e:
                    print(f"Failed to init {name}: {e}")
            except Exception as e:
                print(f"Failed to init {name}: {e}")

    # 3) Try importing likely submodules and common names
    submodules = ["client", "clients", "api", "core", "coinbase"]
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
                    except TypeError:
                        try:
                            return cls(api_key=api_key, api_secret=api_secret)
                        except Exception as e:
                            print(f"Failed to init {cname} from {m}: {e}")
                    except Exception as e:
                        print(f"Failed to init {cname} from {m}: {e}")
        except Exception:
            # ignore import errors for submodule probing
            pass

    # 4) Last resort: dump debug info so we can see what's installed
    debug_module_print()
    raise RuntimeError(
        "Could not find a usable Client class in coinbase_advanced_py. "
        "Check the package API or logs above for available attributes."
    )

# Use the loader
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
if not API_KEY or not API_SECRET:
    print("❌ API_KEY/API_SECRET not set in environment. Set them and redeploy.")
    raise SystemExit(1)

try:
    client = create_coinbase_client(API_KEY, API_SECRET)
    print("✅ Coinbase client created (autodetect).")
except Exception as e:
    print("❌ Failed to create Coinbase client:", e)
    debug_module_print()
    raise
# -------------------------------------------------------------------

# ---------- robust client loader for coinbase_advanced_py ----------
import coinbase_advanced_py as cb
import importlib
import traceback
import sys

def debug_module_print():
    try:
        attrs = dir(cb)
    except Exception as e:
        attrs = f"Unable to dir() coinbase_advanced_py: {e}"
    print("=== coinbase_advanced_py module debug ===")
    print("module repr:", repr(cb))
    print("module file:", getattr(cb, "__file__", "<no __file__>"))
    print("available attributes (dir):")
    print(attrs)
    print("=== end debug ===")

def create_coinbase_client(api_key, api_secret):
    # 1) Try the expected export
    try:
        if hasattr(cb, "Client"):
            print("Using coinbase_advanced_py.Client")
            return cb.Client(api_key, api_secret)
        if hasattr(cb, "client") and hasattr(cb.client, "Client"):
            print("Using coinbase_advanced_py.client.Client")
            return cb.client.Client(api_key, api_secret)
    except Exception as e:
        print("Attempt using cb.Client failed:", e)
        traceback.print_exc()

    # 2) Try common alternative class names on root module
    for name in ("Client", "CoinbaseClient", "Coinbase", "AdvancedClient"):
        if hasattr(cb, name):
            cls = getattr(cb, name)
            try:
                print(f"Trying {name} from root module")
                return cls(api_key, api_secret)
            except TypeError:
                try:
                    return cls(api_key=api_key, api_secret=api_secret)
                except Exception as e:
                    print(f"Failed to init {name}: {e}")
            except Exception as e:
                print(f"Failed to init {name}: {e}")

    # 3) Try importing likely submodules and common names
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
                    except TypeError:
                        try:
                            return cls(api_key=api_key, api_secret=api_secret)
                        except Exception as e:
                            print(f"Failed to init {cname} from {m}: {e}")
                    except Exception as e:
                        print(f"Failed to init {cname} from {m}: {e}")
        except Exception:
            # ignore import errors for submodule probing
            pass

    # 4) Last resort: dump debug info so we can see what's installed
    debug_module_print()
    raise RuntimeError(
        "Could not find a usable Client class in coinbase_advanced_py. "
        "Check the package API or logs above for available attributes."
    )

# Replace your direct cb.Client(...) call with:
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
try:
    client = create_coinbase_client(API_KEY, API_SECRET)
    print("✅ Coinbase client created (autodetect).")
except Exception as e:
    print("❌ Failed to create Coinbase client:", e)
    # keep process alive for diagnostics (or sys.exit(1) if you prefer)
    debug_module_print()
    raise
# -------------------------------------------------------------------
# main.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET in environment variables")

try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase_advanced_py not installed. Check requirements.txt")

# Initialize client
client = cb.Client(API_KEY, API_SECRET)

print("🚀 Coinbase bot started")

# Example: check balances
try:
    balances = client.get_account_balances()
    print("✅ Balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# TODO: Add your trading logic here
