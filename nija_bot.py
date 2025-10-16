#!/usr/bin/env python3
import os
import importlib
import logging
import inspect
from flask import Flask, request, jsonify

# -------------------
# Logging
# -------------------
logger = logging.getLogger("nija_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------------------
# Flask app
# -------------------
app = Flask(__name__)

# -------------------
# Live / Mock mode
# -------------------
USE_MOCK = False  # force live mode

# -------------------
# Attempt to import Coinbase client
# -------------------
try:
    import coinbase_advanced_py as cb_module
    logger.info("✅ Imported coinbase_advanced_py")
except ImportError as e:
    logger.error("❌ Failed to import coinbase_advanced_py: %s", e)
    USE_MOCK = True
    cb_module = None

# -------------------
# Dynamic client discovery
# -------------------
def try_instantiate(obj):
    """Try to instantiate a class/factory with common param names. Return instance or None."""
    if not callable(obj):
        return None
    param_sets = [
        {"api_key": os.getenv("API_KEY"),
         "api_secret": os.getenv("API_SECRET"),
         "api_pem_b64": os.getenv("API_PEM_B64"),
         "sandbox": False},
        {"api_key": os.getenv("API_KEY"),
         "api_secret": os.getenv("API_SECRET"),
         "pem_b64": os.getenv("API_PEM_B64"),
         "sandbox": False},
        {"key": os.getenv("API_KEY"),
         "secret": os.getenv("API_SECRET"),
         "pem": os.getenv("API_PEM_B64")},
        {},  # try no-arg factory
    ]
    for params in param_sets:
        try:
            instance = obj(**params) if params else obj()
            logger.info("Instantiation succeeded for %s with params %s",
                        getattr(obj, "__name__", repr(obj)), params)
            return instance
        except TypeError as e:
            logger.debug("TypeError for %s with params %s: %s",
                         getattr(obj, "__name__", repr(obj)), params, e)
        except Exception as e:
            logger.warning("Instantiation attempt for %s with params %s raised: %s",
                           getattr(obj, "__name__", repr(obj)), params, e)
    return None

client = None
if cb_module and not USE_MOCK:
    # candidate names
    search_names = [n for n in dir(cb_module) if "client" in n.lower()] + [
        "CoinbaseAdvancedClient", "CoinbaseAdvanced", "CoinbaseAdvancedClientV1", "Client", "CoinbaseClient"
    ]
    seen = set()
    candidates = []
    for n in search_names:
        if n not in seen:
            seen.add(n)
            candidates.append(n)

    logger.info("Dynamic client discovery candidates: %s", candidates)

    for name in candidates:
        try:
            if hasattr(cb_module, name):
                obj = getattr(cb_module, name)
                logger.info("Trying candidate: %s -> %s", name, type(obj))
                inst = try_instantiate(obj)
                if inst:
                    client = inst
                    logger.info("✅ Client instantiated from %s", name)
                    break
            else:
                try:
                    sub = importlib.import_module(f"{cb_module.__name__}.{name.lower()}")
                    logger.info("Found submodule: %s", sub.__name__)
                    for subattr in dir(sub):
                        if "client" in subattr.lower() or subattr.lower().endswith("client"):
                            obj = getattr(sub, subattr)
                            logger.info("Trying submodule attribute: %s.%s", sub.__name__, subattr)
                            inst = try_instantiate(obj)
                            if inst:
                                client = inst
                                logger.info("✅ Client instantiated from %s.%s", sub.__name__, subattr)
                                break
                    if client:
                        break
                except Exception as e:
                    logger.debug("No submodule %s.%s: %s", cb_module.__name__, name.lower(), e)
        except Exception as e:
            logger.exception("Error while trying candidate %s: %s", name, e)

    # last resort: any factory-like callable
    if client is None:
        for n in sorted([n for n in dir(cb_module) if not n.startswith("_")])[:400]:
            if n.lower().startswith("create") or n.lower().endswith("client") or n.lower().startswith("from_"):
                try:
                    obj = getattr(cb_module, n)
                    logger.info("Trying other factory-like callable: %s", n)
                    inst = try_instantiate(obj)
                    if inst:
                        client = inst
                        logger.info("✅ Client instantiated from factory-like callable %s", n)
                        break
                except Exception:
                    logger.debug("Skipping %s", n)

if client is None:
    logger.error("❌ Dynamic discovery failed — no usable client instance found.")
    USE_MOCK = True
else:
    logger.info("✅ Dynamic discovery created a client instance: %s", type(client))

# -------------------
# Flask example route
# -------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "live", "mock": USE_MOCK})

# -------------------
# Start guard
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
