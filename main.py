import importlib.util
import sys

def check_coinbase_imports():
    modules_to_check = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase.wallet",
        "coinbase.wallet.client",
    ]
    
    print("=== Checking Coinbase modules ===")
    for mod in modules_to_check:
        spec = importlib.util.find_spec(mod)
        if spec is None:
            print(f"❌ Module NOT found: {mod}")
        else:
            print(f"✅ Module found: {mod}")
    print("=== Done checking ===\n")

# Call this at the very top of main.py before using Coinbase
check_coinbase_imports()
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

find . -name "coinbase*"
