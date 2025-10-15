#!/usr/bin/env python3
# nija_bot.py (clean, uses only dynamic import)

import importlib, sys, os, traceback, pkgutil
from flask import Flask, jsonify

def get_coinbase_module():
    candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    for name in candidates:
        try:
            m = importlib.import_module(name)
            print("DEBUG: imported module ->", name)
            return m
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError("No coinbase-advanced package found; expected one of: " + ", ".join(candidates))

def probe_and_instantiate(module, api_key=None, api_secret=None):
    # Print module summary
    print("DEBUG: module __name__ =", getattr(module, "__name__", None))
    if hasattr(module, "__path__"):
        subs = [m.name for m in pkgutil.iter_modules(module.__path__)]
        print("DEBUG: subpackages:", subs)
    public = [n for n in dir(module) if not n.startswith("_")]
    print("DEBUG: public members (sample):", public[:200])

    # candidate client class/factory names
    client_names = ["Client", "AdvancedClient", "CoinbaseClient", "APIClient", "ClientV2"]
    for cname in client_names:
        cls = getattr(module, cname, None)
        if cls:
            print(f"DEBUG: found candidate class {cname} on {module.__name__}")
            if api_key and api_secret:
                try:
                    inst = cls(api_key, api_secret)
                    print(f"DEBUG: instantiated {cname}")
                    return inst
                except Exception as e:
                    print(f"DEBUG: failed to instantiate {cname} with (key,secret): {type(e).__name__}: {e}")
            else:
                try:
                    inst = cls()  # maybe default constructor
                    print(f"DEBUG: instantiated {cname} without credentials")
                    return inst
                except Exception as e:
                    print(f"DEBUG: {cname} default constructor failed: {type(e).__name__}: {e}")

    # try submodules if present (e.g. coinbase.advanced)
    if hasattr(module, "__path__"):
        for finder, name, ispkg in pkgutil.iter_modules(module.__path__):
            fullname = f"{module.__name__}.{name}"
            try:
                sub = importlib.import_module(fullname)
                print("DEBUG: imported submodule", fullname)
                # try same client discovery on submodule
                for cname in client_names:
                    cls = getattr(sub, cname, None)
                    if cls:
                        try:
                            inst = cls(api_key, api_secret) if api_key and api_secret else cls()
                            print(f"DEBUG: instantiated {fullname}.{cname}")
                            return inst
                        except Exception as e:
                            print(f"DEBUG: instantiation {fullname}.{cname} failed: {e}")
            except Exception as e:
                print("DEBUG: couldn't import submodule", fullname, e)

    # factory functions
    for fname in ("Client", "create_client", "create_client_instance", "from_api_key"):
        fn = getattr(module, fname, None)
        if callable(fn):
            try:
                inst = fn(api_key, api_secret) if api_key and api_secret else fn()
                print(f"DEBUG: created client via factory {fname}")
                return inst
            except Exception as e:
                print(f"DEBUG: factory {fname} raised: {type(e).__name__}: {e}")

    return None

def extract_balances(client):
    # try several safe read-only methods
    candidates = ["get_account_balances","get_accounts","list_accounts","accounts","list_wallets","get_wallets"]
    for mname in candidates:
        m = getattr(client, mname, None)
        if callable(m):
            try:
                res = m()
                print("DEBUG: called client.%s() -> %s" % (mname, type(res).__name__))
                # normalize results (best-effort)
                if isinstance(res, dict):
                    return res
                if isinstance(res, (list, tuple)):
                    out = {}
                    for item in res:
                        if isinstance(item, dict):
                            cur = item.get("currency") or item.get("currency_code") or item.get("symbol")
                            bal = item.get("balance") or item.get("available") or item.get("amount")
                            if cur:
                                out[cur] = bal
                        else:
                            cur = getattr(item, "currency", None) or getattr(item, "currency_code", None)
                            bal = getattr(item, "balance", None) or getattr(item, "available", None)
                            if cur:
                                out[cur] = bal
                    if out:
                        return out
            except Exception as e:
                print(f"DEBUG: calling client.{mname} raised {type(e).__name__}: {e}")
    # nothing found
    return {}

# -------------------
# Main
# -------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

try:
    cbmod = get_coinbase_module()
    client = probe_and_instantiate(cbmod, API_KEY, API_SECRET)
    if client:
        LIVE_TRADING = True
        print("🟢 Live client initialized from module:", cbmod.__name__)
    else:
        print("WARN: coinbase module present but no usable client found; falling back to MockClient")
except Exception as e:
    print("WARN: coinbase import/instantiation failed:", type(e).__name__, e)
    traceback.print_exc()

if not client:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
        def get_accounts(self):
            return [{"currency":"USD","balance":10000.0},{"currency":"BTC","balance":0.05}]
    client = MockClient()

balances = extract_balances(client) or {}
print("💰 Starting balances:", balances)

app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({"status":"NIJA Bot is running!", "LIVE_TRADING": LIVE_TRADING, "balances": balances})

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
