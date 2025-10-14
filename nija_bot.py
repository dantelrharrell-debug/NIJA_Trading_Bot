# -------------------
# Robust Coinbase import (try multiple likely module names)
# -------------------
_coinbase_module = None
_coinbase_import_name = None
_for_candidates = [
    "coinbase_advanced_py",   # expected
    "coinbase_advanced",      # possible alternate
    "coinbase",               # generic
    "coinbase_advanced_py_client",
    "coinbasepro",            # sometimes used by other libs
]

import importlib
for _name in _for_candidates:
    try:
        _mod = importlib.import_module(_name)
        _coinbase_module = _mod
        _coinbase_import_name = _name
        print(f"✅ Imported Coinbase module using '{_name}'")
        break
    except Exception:
        # intentionally silent for each try to continue trying next candidate
        pass

if _coinbase_module is None:
    print("❌ coinbase module not found under tried names:", _for_candidates)
    # Fallback to mock mode; we set USE_MOCK True so the rest of the app uses MockClient
    USE_MOCK = True
else:
    # If we imported a module, try to init the client using common constructor names
    try:
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        if not API_KEY or not API_SECRET:
            raise ValueError("Missing API_KEY or API_SECRET in env")

        # common client constructors:
        client = None
        for constructor in ("Client", "ClientV2", "CoinbaseClient"):
            if hasattr(_coinbase_module, constructor):
                client = getattr(_coinbase_module, constructor)(API_KEY, API_SECRET)
                break

        # try fallback names or factory functions some libs use
        if client is None and hasattr(_coinbase_module, "create_client"):
            client = _coinbase_module.create_client(API_KEY, API_SECRET)

        if client is None:
            # Last attempt: maybe module itself behaves as client
            if callable(_coinbase_module):
                try:
                    client = _coinbase_module(API_KEY, API_SECRET)
                except Exception:
                    client = None

        if client is None:
            raise RuntimeError("Could not initialize client from imported module (constructor not found)")

        LIVE_TRADING = True
        print(f"🚀 Coinbase client initialized via module '{_coinbase_import_name}'. LIVE_TRADING enabled.")
    except Exception as e:
        print("❌ Failed to connect live Coinbase client:", e)
        import traceback as _tb
        _tb.print_exc()
        USE_MOCK = True
