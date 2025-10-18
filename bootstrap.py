#!/usr/bin/env python3
import os
import base64
import logging

logger = logging.getLogger("nija_startup")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(ch)

USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"

# Write PEM from base64 env var (if provided)
pem_b64 = os.getenv("API_PEM_B64")
pem_path = "/tmp/my_coinbase_key.pem"
if pem_b64:
    try:
        with open(pem_path, "wb") as f:
            f.write(base64.b64decode(pem_b64))
        os.chmod(pem_path, 0o600)
        logger.info("✅ PEM written to %s", pem_path)
    except Exception as e:
        logger.exception("Failed to write PEM: %s", e)

coinbase_client = None
if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        API_KEY = os.getenv("API_KEY")
        # adapt this call to the library's constructor:
        coinbase_client = cb.Client(api_key=API_KEY, private_key_path=pem_path)
        logger.info("✅ coinbase_advanced_py imported and client initialized.")
    except Exception as e:
        logger.exception("DEBUG: coinbase_advanced_py not importable or failed to init: %s", e)
        try:
            import coinbase
            logger.info("DEBUG: legacy 'coinbase' package import OK")
        except Exception as e2:
            logger.exception("legacy coinbase import failed: %s", e2)
        USE_MOCK = True

if USE_MOCK or coinbase_client is None:
    logger.warning("WARN: No live Coinbase client initialized; falling back to MockClient")
    # initialize your MockClient here
else:
    logger.info("🔒 LIVE_TRADING = %s", LIVE_TRADING)
