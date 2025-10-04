# start_bot.py
import os
import sys
import logging
from uvicorn import run

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("start_bot")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("PORT", 10000)))
    log.info("Starting NIJA Trading Bot uvicorn on port %s", port)
    # This will import main and let FastAPI startup run
    run("main:app", host="0.0.0.0", port=port, log_level="info")
