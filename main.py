import sys
print("[startup] Starting main.py...", file=sys.stderr)
import os
import sys
import pkgutil
import importlib
import traceback
from flask import Flask, jsonify, request

app = Flask(__name__)

def lazy_load_coinbase_client(verbose=True):
   # Initialize client
client = lazy_load_coinbase_client(verbose=True)

# <-- DEBUG logs immediately after initialization
if client is None:
    print("[DEBUG] Coinbase client failed to initialize!", file=sys.stderr)
else:
    print("[DEBUG] Coinbase client initialized successfully!", file=sys.stderr) """
    Detect any installed Coinbase client, try all known constructors,
    and return the client instance (or None if nothing works).
    """
    # List all installed modules containing "coinbase"
    installed_modules = [m.name for m in pkgutil.iter_modules() if "coinbase" in m.name.lower()]
    if verbose:
        print(f"[startup] Installed coinbase-like modules: {installed_modules}", file=sys.stderr)

    candidates = [
        "coinbase_advancedtrade.client",
        "coinbase_advanced_trade.client",
        "coinbase_advanced_py.client",
        "coinbase_advanced.client",
        "coinbase.client",
    ]

    for modname in candidates:
        try:
            mod = importlib.import_module(modname)
            if verbose:
                print(f"[startup] Imported module: {modname}", file=sys.stderr)

            # Try known client class names
            for attr in ("Client", "CoinbaseAdvancedTradeAPIClient", "RESTClient", "CoinbaseClient"):
                if hasattr(mod, attr):
                    C = getattr(mod, attr)
                    if verbose:
                        print(f"[startup] Found class: {modname}.{attr}", file=sys.stderr)

                    constructors = [
                        lambda C: C(
                            api_key=os.getenv("COINBASE_API_KEY", ""),
                            api_secret=os.getenv("COINBASE_API_SECRET", ""),
                            passphrase=os.getenv("COINBASE_API_PASSPHRASE", "")
                        ),
                        lambda C: C(
                            api_key=os.getenv("COINBASE_API_KEY", ""),
                            api_secret=os.getenv("COINBASE_API_SECRET", "")
                        ),
                        lambda C: C.from_cloud_api_keys(
                            os.getenv("COINBASE_API_KEY", ""),
                            os.getenv("COINBASE_API_SECRET", "")
                        ) if hasattr(C, "from_cloud_api_keys") else (_ for _ in ()).throw(Exception()),
                        lambda C: C.from_keys(
                            os.getenv("COINBASE_API_KEY", ""),
                            os.getenv("COINBASE_API_SECRET", "")
                        ) if hasattr(C, "from_keys") else (_ for _ in ()).throw(Exception())
                    ]

                    for i, ctor in enumerate(constructors):
                        try:
                            client_instance = ctor(C)
                            if verbose:
                                print(f"[startup] Successfully initialized client using constructor #{i+1}", file=sys.stderr)
                            return client_instance
                        except Exception as e:
                            if verbose:
                                print(f"[startup] Constructor #{i+1} failed for {modname}.{attr}:\n{traceback.format_exc()}", file=sys.stderr)
            
            # If module itself is callable
            if callable(mod):
                if verbose:
                    print(f"[startup] Module itself is callable: {modname}", file=sys.stderr)
                return mod()

        except Exception as e:
            if verbose:
                print(f"[startup] Failed to import module {modname}:\n{traceback.format_exc()}", file=sys.stderr)

    # Nothing worked
    if verbose:
        print("[startup] No Coinbase client could be initialized.", file=sys.stderr)
    return None

# Initialize client
client = lazy_load_coinbase_client(verbose=True)

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/status")
def status():
    if client is None:
        return jsonify({"status":"error","message":"Coinbase client not initialized"}), 500
    return jsonify({"status":"connected"})

@app.route("/webhook", methods=["POST"])
def webhook():
    if client is None:
        return jsonify({"status":"error","message":"Coinbase client not initialized"}), 500
    
    data = request.json or {}
    symbol = data.get("symbol")
    action = data.get("action")
    size = data.get("size")
    
    if not symbol or not action:
        return jsonify({"status":"ignored","message":"missing symbol or action"}), 400
    
    try:
        if hasattr(client, "place_order"):
            order = client.place_order(product_id=symbol, side=action, size=size, type="market")
            return jsonify({"status":"success","order":order})
        if hasattr(client, "create_limit_order"):
            order = client.create_limit_order(client_order_id="webhook",
                                              product_id=symbol,
                                              side=action,
                                              limit_price="0",
                                              base_size=size)
            return jsonify({"status":"success","order":order})
        return jsonify({"status":"error","message":"no known order method on client"}), 500
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500
