# start_bot.py
import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("Starting NIJA Trading Bot via uvicorn on port", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
