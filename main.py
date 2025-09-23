# main.py
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello Render!"
print("Hello world")<<'PYEOF'
# main.py — robust loader that won't crash if coinbase module name differs
import os, sys, importlib, traceback, pkgutil
from flask import Flask, jsonify, request

# debug: list installed coinbase-like modules
installed_coinbase_modules = [m.name for m in pkgutil.iter_modules() if "coinbase" in m.name or "coinbase" in m.name.replace("_","")]

candidates = [
    "coinbase_advanced_trade.client",
    "coinbase_advancedtrade.client",
    "coinbase_advanced_py",
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase_advanced",
    "coinbaseadvanced.client",
    "coinbase.client",
]

ClientClass = None
found_source = None

for modname in candidates:
    try:
        mod = importlib.import_module(modname)
        for attr in ("Client", "CoinbaseAdvancedTradeAPIClient", "RESTClient", "CoinbaseClient", "ClientV1"):
            if hasattr(mod, attr):
                ClientClass = getattr(mod, attr)
                found_source = f"{modname}.{attr}"
                break
        if ClientClass is None and callable(mod):
            ClientClass = mod
            found_source = f"{modname} (module callable)"
        if ClientClass:
            break
    except Exception:
        pass

if found_source:
    print(f"[startup] Found Coinbase client: {found_source}", file=sys.stderr)
else:
    print(f"[startup] No Coinbase client found. Installed coinbase modules: {installed_coinbase_modules}", file=sys.stderr)

client = None
if ClientClass:
    API_KEY = os.getenv("COINBASE_API_KEY", "")
    API_SECRET = os.getenv("COINBASE_API_SECRET", "")
    API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE", "")

    constructors = [
        lambda C: C(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE),
        lambda C: C(api_key=API_KEY, api_secret=API_SECRET),
        lambda C: C.from_cloud_api_keys(API_KEY, API_SECRET) if hasattr(C, "from_cloud_api_keys") else (_ for _ in ()).throw(Exception()),
        lambda C: C.from_api_key_and_secret(API_KEY, API_SECRET) if hasattr(C, "from_api_key_and_secret") else (_ for _ in ()).throw(Exception()),
        lambda C: C.from_keys(API_KEY, API_SECRET) if hasattr(C, "from_keys") else (_ for _ in ()).throw(Exception()),
    ]

    init_errors = []
    for ctor in constructors:
        try:
            client = ctor(ClientClass)
            print("[startup] Coinbase client initialized.", file=sys.stderr)
            break
        except Exception:
            init_errors.append(traceback.format_exc())

    if client is None:
        print("[startup] Failed to initialize Coinbase client. Constructor traces:", file=sys.stderr)
        for e in init_errors:
            print(e, file=sys.stderr)

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

@app.route("/status")
def status():
    if client is None:
        return jsonify({"status":"error","message":"Coinbase client not initialized. See logs."}), 500
    for name in ("get_accounts","list_accounts","accounts","get_all_accounts"):
        if hasattr(client, name):
            try:
                res = getattr(client, name)()
                return jsonify({"status":"connected","accounts":res})
            except Exception as e:
                return jsonify({"status":"error","message":str(e)}), 500
    return jsonify({"status":"connected","message":"client exists but no accounts method"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    if client is None:
        return jsonify({"status":"error","message":"Coinbase client not initialized"}), 500
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
            order = client.create_limit_order(client_order_id="webhook", product_id=symbol, side=action, limit_price="0", base_size=size)
            return jsonify({"status":"success","order":order})
        return jsonify({"status":"error","message":"no known order method on client"}), 500
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500
