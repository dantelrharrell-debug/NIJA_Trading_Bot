import os
import logging
from fastapi import FastAPI
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nija")

# Attempt to import Coinbase client
try:
    import coinbase_advanced_py as cb
    coinbase_client = cb.Client(
        os.getenv("API_KEY"),
        os.getenv("API_SECRET")
    )
    logger.info("coinbase_advanced_py loaded successfully")
except ModuleNotFoundError:
    cb = None
    coinbase_client = None
    logger.exception("coinbase_advanced_py not installed — trading disabled.")
except Exception as e:
    cb = None
    coinbase_client = None
    logger.exception(f"Coinbase client init failed: {e}")

# FastAPI app
app = FastAPI()

@app.get("/health")
def health():
    return {
        "status": "ok",
        "coinbase_client": bool(coinbase_client)
    }

@app.get("/")
def root():
    return {"message": "NIJA Trading Bot API running"}
