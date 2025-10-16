#!/usr/bin/env python3
"""
nija_bot.py
Robust Render-ready Flask app for NIJA trading bot.

- Auto-detects coinbase package in the venv.
- Introspects the imported coinbase module (safe, no network calls).
- Attempts multiple import names and constructors.
- Falls back to mock mode safely if live client cannot be initialized.
- Adds simple file + console logging for Render logs.
"""

import os
import sys
import traceback
import importlib
import inspect
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -------------------
# Load environment
# -------------------
load_dotenv()

# -------------------
# Logging (console + file)
# -------------------
LOG_FILE = os.getenv("NIJA_LOG_FILE", "nija_bot.log")
logger = logging.getLogger("nija_bot")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# Console handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt)
logger.addHandler(ch)

# Rotating file handler (keeps logs small)
fh = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3)
fh.setFormatter(fmt)
logger.addHandler(fh)

logger.info("Starting NIJA bot...")

# -------------------
# Determine mock mode flag from env (default True for safety)
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
logger.info("USE_MOCK initial value: %s", USE_MOCK)

# -------------------
# Ensure venv site-packages is on sys.path (adjust python version as needed)
# -------------------
try:
    venv_site = os.path.join(os.getcwd(), ".venv", "lib", f"python3.11", "site-packages")
    if venv_site not in sys.path:
        sys.path.insert(0, venv_site)
    logger.info("Ensured venv site-packages on sys.path: %s", venv_site)
except Exception:
    logger.exception("Failed to configure venv site-packages path.")

# -------------------
# Robust Coinbase import + introspection + client init
# -------------------
client = None
cb_module = None
if not USE_MOCK:
    possible_names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    import_errors = {}

    for name in possible_names:
        try:
            cb_module = importlib.import_module(name)
            logger.info("✅ Imported Coinbase module as: %s", name)
            break
        except Exception as e:
            import_errors[name] = repr(e)

    if cb_module is None:
        logger.error("❌ Could not import coinbase module. Errors: %s", import_errors)
        logger.info("Falling back to MOCK mode for safety.")
        USE_MOCK = True
    else:
        # -------------------
        # Introspect imported module (safe - no network calls)
        # -------------------
        try:
            logger.info("Introspecting imported coinbase module: %s", cb_module.__name__)
            names = sorted([n for n in dir(cb_module) if not n.startswith("_")])
            logger.info("Top-level names: %s", names[:200])
            for n in names:
                obj = getattr(cb_module, n)
                if inspect.isclass(obj) or inspect.isfunction(obj) or callable(obj):
                    try:
                        sig = inspect.signature(obj)
                    except (ValueError, TypeError):
                        sig = "<no signature available>"
                    logger.info("  %s: %s | signature: %s", n, type(obj).__name__, sig)
        except Exception:
            logger.exception("Error during coinbase introspection")

        # -------------------
        # Try to find a usable client class or factory
        # -------------------
        try:
            candidate_attrs = [
                "CoinbaseAdvancedClient",
                "CoinbaseAdvanced",
                "CoinbaseAdvancedClientV1",
                "Client",
            ]
            for attr in candidate_attrs:
                if hasattr(cb_module, attr):
                    cls_or_factory = getattr(cb_module, attr)
                    try:
                        # Try common constructor patterns
                        client = cls_or_factory(
                            api_key=os.getenv("API_KEY"),
                            api_secret=os.getenv("API_SECRET"),
                            api_pem_b64=os.getenv("API_PEM_B64"),
                            sandbox=False,
                        )
                        logger.info("✅ Initialized Coinbase client using %s.%s", cb_module.__name__, attr)
                        break
                    except TypeError:
                        # Try alternative param name
                        try:
                            client = cls_or_factory(
                                api_key=os.getenv("API_KEY"),
                                api_secret=os.getenv("API_SECRET"),
                                pem_b64=os.getenv("API_PEM_B64"),
                                sandbox=False,
                            )
                            logger.info("✅ Initialized Coinbase client (alt params) using %s.%s", cb_module.__name__, attr)
                            break
                        except Exception as e:
                            logger.warning("Instantiation of %s.%s failed: %s", cb_module.__name__, attr, e)
                    except Exception as e:
                        logger.warning("Error instantiating %s.%s: %s", cb_module.__name__, attr, e)

            # If not instantiated yet, try common factory functions
            if client is None:
                for funcname in ["Client", "create_client", "from_env"]:
                    if hasattr(cb_module, funcname):
                        try:
                            factory = getattr(cb_module, funcname)
                            client = factory()
                            logger.info("✅ Initialized client via factory %s.%s()", cb_module.__name__, funcname)
                            break
                        except Exception as e:
                            logger.warning("Factory %s.%s() failed: %s", cb_module.__name__, funcname, e)

            if client is None:
                logger.error("❌ Coinbase module imported but no usable client was instantiated.")
                USE_MOCK = True
        except Exception:
            logger.exception("Unexpected error while initializing Coinbase client.")
            USE_MOCK = True
else:
    logger.info("ℹ️ Running in MOCK mode (no real trades)")

# -------------------
# Provide a safe mock client when needed
# -------------------
class MockClient:
    def __init__(self):
        self.name = "MockClient"

    def place_order(self, *args, **kwargs):
        logger.info("MOCK place_order called with args=%s kwargs=%s", args, kwargs)
        return {"status": "mocked", "order_id": "mock-" + os.urandom(4).hex()}

    def get_account(self, *args, **kwargs):
        logger.info("MOCK get_account called")
        return {"balance": 1000.0, "currency": "USD"}

    def __repr__(self):
        return "<MockClient>"

if USE_MOCK or client is None:
    client = MockClient()
    logger.info("Using MockClient (safe)")

# -------------------
# Flask app setup
# -------------------
app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/", methods=["GET"])
def index():
    """Healthcheck / status"""
    try:
        return jsonify({"status": "NIJA Bot running", "mock": isinstance(client, MockClient)}), 200
    except Exception:
        logger.exception("Error in index route")
        return jsonify({"status": "error"}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """Primary webhook endpoint that triggers trading logic (mock safe)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
        if secret != WEBHOOK_SECRET:
            logger.warning("Unauthorized webhook attempt.")
            return jsonify({"error": "unauthorized"}), 401

        event_type = data.get("type", "unknown")
        logger.info("🔔 Received webhook event: %s", event_type)

        # Example: if event says place an order
        if event_type == "place_order":
            params = data.get("params", {})
            logger.info("Attempting to place order with params: %s", params)
            try:
                result = client.place_order(**params)
                logger.info("Order result: %s", result)
                return jsonify({"status": "ok", "result": result}), 200
            except Exception as e:
                logger.exception("Error placing order")
                return jsonify({"error": "order_failed", "detail": str(e)}), 500

        # For other events, just echo
        return jsonify({"status": "received", "event": event_type, "data": data}), 200

    except Exception as e:
        logger.exception("Unhandled exception in webhook")
        return jsonify({"error": "internal_error", "detail": str(e)}), 500

# -------------------
# Run locally (only when executed directly)
# -------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info("Running Flask dev server on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port)
