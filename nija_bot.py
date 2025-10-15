# ---------------------------
# Coinbase client initialization (paste here)
# ---------------------------
import os
import sys
import logging
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# Candidate top-level import names to try (common variants)
CANDIDATES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase_advanced_py.client",
    "coinbase.client",
]

_real_cb_module = None
_real_cb_name = None
for name in CANDIDATES:
    try:
        __import__(name)
        _real_cb_module = sys.modules[name]
        _real_cb_name = name
        logger.info("Imported Coinbase module as '%s' (module: %s)", name, getattr(_real_cb_module, "__file__", repr(_real_cb_module)))
        break
    except Exception as e:
        logger.debug("Import attempt failed for %s: %s", name, e)
        # continue to next candidate

# Minimal MockClient for safety
class MockClient:
    def __init__(self):
        logger.warning("MockClient initialized (NO LIVE TRADING).")

    def get_account_balances(self):
        return {"USD": 1000.0, "BTC": 0.0}

    def place_order(self, *args, **kwargs):
        logger.info("MockClient.place_order called with args=%s kwargs=%s", args, kwargs)
        return {"status": "mock", "args": args, "kwargs": kwargs}

COINBASE_CLIENT = None
LIVE_TRADING = False

# If we found a module, try to create a client only if credentials exist
if _real_cb_module is not None:
    # env var names your code expects
    API_KEY = os.getenv("COINBASE_API_KEY")
    API_SECRET = os.getenv("COINBASE_API_SECRET")
    API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")
    API_PEM_B64 = os.getenv("COINBASE_PRIVATE_KEY_PEM_BASE64")  # optional

    if not (API_KEY and (API_SECRET or API_PEM_B64)):
        logger.warning("Coinbase package found (%s) but credentials missing. Falling back to MockClient.", _real_cb_name)
        COINBASE_CLIENT = MockClient()
    else:
        # Try a few common constructors / client factories
        try:
            if hasattr(_real_cb_module, "Client"):
                COINBASE_CLIENT = _real_cb_module.Client(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE)
            elif hasattr(_real_cb_module, "rest") and hasattr(_real_cb_module.rest, "Client"):
                COINBASE_CLIENT = _real_cb_module.rest.Client(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE)
            elif hasattr(_real_cb_module, "CoinbaseAdvancedAPIClient"):
                COINBASE_CLIENT = _real_cb_module.CoinbaseAdvancedAPIClient(
                    api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE
                )
            else:
                # last-resort: try module-level factory function names
                created = False
                for fn in ("create_client", "Client", "RestClient"):
                    factory = getattr(_real_cb_module, fn, None)
                    if factory:
                        try:
                            COINBASE_CLIENT = factory(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE)
                            created = True
                            break
                        except Exception:
                            continue
                if not created and COINBASE_CLIENT is None:
                    raise RuntimeError("No known Client constructor found on module: " + str(_real_cb_name))
            LIVE_TRADING = True
            logger.info("Real Coinbase client initialized (LIVE_TRADING=True).")
        except Exception as e:
            logger.exception("Failed to construct Coinbase client; falling back to MockClient. Exception: %s", e)
            COINBASE_CLIENT = MockClient()
else:
    # No package imported
    COINBASE_CLIENT = MockClient()

# Now COINBASE_CLIENT and LIVE_TRADING are available for the rest of the app
# ---------------------------
# End Coinbase initialization
# ---------------------------
#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")  # if required

# ---------------------------
# Determine client
# ---------------------------
coinbase_client = None

if not USE_MOCK and API_KEY and API_SECRET:
    try:
        import coinbase_advanced_py as cb
        coinbase_client = cb.Client(
            api_key=API_KEY,
            api_secret=API_SECRET,
            api_passphrase=API_PASSPHRASE  # optional
        )
        print("✅ Coinbase client initialized (live trading)")
    except Exception as e:
        print("❌ Failed to initialize Coinbase client:", e)
        USE_MOCK = True

# ---------------------------
# Define MockClient fallback
# ---------------------------
class MockClient:
    def __init__(self):
        print("⚠️ MockClient initialized (no live trading)")

    def get_account(self):
        return {"balance": 0}

    def place_order(self, *args, **kwargs):
        print(f"Mock order: args={args}, kwargs={kwargs}")
        return {"id": "mock_order"}

if coinbase_client is None:
    coinbase_client = MockClient()
    USE_MOCK = True

print("sys.executable:", sys.executable)
print("sys.path:", sys.path)
print("USE_MOCK:", USE_MOCK)

# ---------------------------
# Flask setup
# ---------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "NIJA Bot is running!"

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)

#!/usr/bin/env python3
import os
import sys
from flask import Flask, jsonify
from dotenv import load_dotenv

# -------------------
# Load environment variables
# -------------------
load_dotenv()
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

# -------------------
# Coinbase client setup
# -------------------
coinbase_client = None

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        coinbase_client = cb
        print("✅ Imported coinbase_advanced_py")
    except ModuleNotFoundError:
        try:
            import coinbase_advanced as cb
            coinbase_client = cb
            print("✅ Imported coinbase_advanced")
        except ModuleNotFoundError:
            print("❌ Failed to import Coinbase client, falling back to MockClient")
            USE_MOCK = True

# -------------------
# Define MockClient (fallback)
# -------------------
class MockClient:
    def __init__(self):
        print("⚠️ MockClient initialized (no live trading)")

    def get_account(self):
        return {"balance": 0}

    def place_order(self, *args, **kwargs):
        print(f"Mock order executed: args={args}, kwargs={kwargs}")
        return {"id": "mock_order", "args": args, "kwargs": kwargs}

if USE_MOCK or coinbase_client is None:
    coinbase_client = MockClient()

# -------------------
# Flask app setup
# -------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "NIJA Bot is running!"

@app.route("/test_order")
def test_order():
    """
    Place a test order using the coinbase_client (or MockClient).
    """
    result = coinbase_client.place_order(
        product_id="BTC-USD",
        side="buy",
        price="1",
        size="0.001"
    )
    return jsonify({"result": result})

# -------------------
# Debug info (optional)
# -------------------
print("🚀 Starting NIJA Bot")
print("sys.executable:", sys.executable)
print("sys.path:", sys.path)
print("USE_MOCK:", USE_MOCK)

# -------------------
# Start Flask server
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
