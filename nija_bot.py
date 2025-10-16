import os
import sys
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

COINBASE_CLIENT = None
LIVE_TRADING = False

try:
    import coinbase_advanced_py as cb
    API_KEY = os.getenv("COINBASE_API_KEY")
    API_SECRET = os.getenv("COINBASE_API_SECRET")
    API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")
    API_PEM_B64 = os.getenv("COINBASE_PRIVATE_KEY_PEM_BASE64")

    if API_KEY and (API_SECRET or API_PEM_B64):
        COINBASE_CLIENT = cb.Client(
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=API_PASSPHRASE
        )
        LIVE_TRADING = True
        logger.info("✅ Coinbase client initialized (LIVE TRADING)")
    else:
        raise ValueError("Credentials missing")
except Exception as e:
    logger.warning("⚠️ Failed to initialize Coinbase client, using MockClient. Exception: %s", e)

# Minimal MockClient fallback
class MockClient:
    def get_account_balances(self):
        return {"USD": 1000.0, "BTC": 0.0}

    def place_order(self, *args, **kwargs):
        logger.info("Mock order executed: args=%s kwargs=%s", args, kwargs)
        return {"status": "mock", "args": args, "kwargs": kwargs}

if COINBASE_CLIENT is None:
    COINBASE_CLIENT = MockClient()
    LIVE_TRADING = False
