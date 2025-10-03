# nija_bot.py

import os
import logging
from fastapi import FastAPI

# ----------------------------
# Logging setup
# ----------------------------
logger = logging.getLogger("nija")
logging.basicConfig(level=logging.INFO)

# ----------------------------
# Safe import for coinbase client
# ----------------------------
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    cb = None
    logger.exception("coinbase_advanced_py not installed — trading disabled until dependency fixed.")

# ----------------------------
# FastAPI app setup
# ----------------------------
app = FastAPI(title="NIJA Trading Bot")

# ----------------------------
# Health endpoint
# ----------------------------
@app.get("/health")
def health():
    """
    Returns basic health info and whether the coinbase client is available
    """
    return {
        "status": "ok",
        "coinbase_client": bool(cb)
    }

# ----------------------------
# Example main function (optional)
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
