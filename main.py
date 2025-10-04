import logging
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# --- Coinbase client detection ---
coinbase_client_detected = False
coinbase_module = None
CoinbaseClient = None

try:
    import coinbase_advanced_py
    from coinbase_advanced_py import Client as CoinbaseClient
    coinbase_client_detected = True
    coinbase_module = "coinbase_advanced_py"
    logging.info(f"Discovered Coinbase client: {coinbase_module}")
except ModuleNotFoundError:
    logging.warning(
        "No Coinbase client library found. Tried coinbase_advanced_py. Trading will be disabled."
    )

# Optional: check if API keys are set
if coinbase_client_detected:
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    if not API_KEY or not API_SECRET:
        logging.warning("Coinbase API_KEY or API_SECRET missing. Trading will be disabled.")
        coinbase_client_detected = False

# --- FastAPI endpoints ---
@app.get("/")
def root():
    return {
        "status": "Bot is live",
        "coinbase_client_detected": coinbase_client_detected,
        "coinbase_module": coinbase_module,
    }

@app.get("/diag")
def diag():
    """
    Returns detailed diagnostic info for debugging Coinbase client.
    """
    return {
        "coinbase_client_detected": coinbase_client_detected,
        "coinbase_module": coinbase_module,
        "python_version": os.sys.version,
        "env_api_key_set": bool(os.getenv("API_KEY")),
        "env_api_secret_set": bool(os.getenv("API_SECRET")),
    }

# --- Optional: Trading placeholder ---
if coinbase_client_detected:
    logging.info("Trading ENABLED.")
else:
    logging.warning("Trading DISABLED. Coinbase client not detected or API keys missing.")
