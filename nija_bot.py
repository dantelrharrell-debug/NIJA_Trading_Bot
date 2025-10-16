#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask, request, jsonify

from dotenv import load_dotenv
load_dotenv()

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

# -------------------
# Robust Coinbase import + client init
# -------------------
import importlib
# ensure venv site-packages is available (adjust python version if needed)
venv_site = os.path.join(os.getcwd(), ".venv", "lib", f"python3.11", "site-packages")
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

_possible_names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
cb_module = None
cb_import_errors = {}
for name in _possible_names:
    try:
        cb_module = importlib.import_module(name)
        print(f"✅ Imported Coinbase module as: {name}")
        break
    except Exception as e:
        cb_import_errors[name] = repr(e)

if cb_module is None:
    print("❌ Could not import coinbase module. Import attempts raised:")
    for k, v in cb_import_errors.items():
        print(f" - {k}: {v}")
    print("ℹ️ Falling back to MOCK mode (USE_MOCK=True).")
    USE_MOCK = True
else:
    client = None
    candidate_attrs = ["CoinbaseAdvancedClient", "CoinbaseAdvanced", "CoinbaseAdvancedClientV1", "Client"]
    for attr in candidate_attrs:
        if hasattr(cb_module, attr):
            try:
                cls = getattr(cb_module, attr)
                try:
                    client = cls(
                        api_key=os.getenv("API_KEY"),
                        api_secret=os.getenv("API_SECRET"),
                        api_pem_b64=os.getenv("API_PEM_B64"),
                        sandbox=False
                    )
                except TypeError:
                    try:
                        client = cls(
                            api_key=os.getenv("API_KEY"),
                            api_secret=os.getenv("API_SECRET"),
                            pem_b64=os.getenv("API_PEM_B64"),
                            sandbox=False
                        )
                    except Exception as e:
                        print(f"⚠️ Instantiation of {attr} failed: {e!r}")
                        client = None
                if client:
                    print(f"✅ Successfully initialized Coinbase client using {name}.{attr}")
                    break
            except Exception as e:
                print(f"⚠️ Error while trying to use {name}.{attr}: {e!r}")

    if client is None:
        for funcname in ["Client", "create_client", "from_env"]:
            if hasattr(cb_module, funcname):
                try:
                    factory = getattr(cb_module, funcname)
                    client = factory()
                    print(f"✅ Initialized client via factory {name}.{funcname}()")
                    break
                except Exception as e:
                    print(f"⚠️ Factory {name}.{funcname}() failed: {e!r}")
    if client is None:
        print("❌ Coinbase module imported but no usable client was instantiated. Falling back to MOCK mode.")
        USE_MOCK = True


# -------------------
# Flask app setup
# -------------------
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"status": "success", "data": data})
