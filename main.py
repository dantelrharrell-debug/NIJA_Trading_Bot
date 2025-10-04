# main.py
import os
import sys
import logging
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nija_main")

app = FastAPI(title="NIJA Trading Bot")

@app.get("/")
def root():
    return {"status":"ok", "message":"NIJA Trading Bot alive"}

@app.get("/diag")
def diag():
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.splitlines()[0],
        "cwd": os.getcwd(),
        "sys_path_sample": sys.path[:6],
        "env": {
            "PORT": os.environ.get("PORT"),
            "LIVE_TRADING": os.environ.get("LIVE_TRADING"),
            "API_KEY_present": bool(os.environ.get("API_KEY")),
        }
    }
