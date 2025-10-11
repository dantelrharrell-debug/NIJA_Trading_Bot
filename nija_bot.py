#!/usr/bin/env python3
# ---------- environment & imports (paste this at top of nija_bot.py) ----------
import os
import sys
from pathlib import Path

# optional: load .env for local testing (Render will use environment variables)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded local .env (if present)")
except Exception:
    # it's OK if python-dotenv isn't available on Render
    print("ℹ️ python-dotenv not installed or .env missing (OK on Render)")

# Read environment variables
API_KEY = os.getenv("API_KEY") or None
API_SECRET = os.getenv("API_SECRET") or None

# API_PEM should contain the full PEM file as a string (including BEGIN/END lines),
# or be empty/None if you are not using PEM auth.
API_PEM = os.getenv("API_PEM")  # multiline string allowed

# Flags
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

# Basic diagnostics (masked)
def _mask(s):
    if not s:
        return "<none>"
    if len(s) <= 8:
        return "****"
    return s[:4] + "..." + s[-3:]

print(f"🔐 API_KEY={_mask(API_KEY)}, API_SECRET={_mask(API_SECRET)}, API_PEM={'present' if API_PEM else 'none'}")
print(f"⚙️ DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX}")

# Ensure vendor path is present if you expect vendored module
ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

# Import the package's RESTClient class we will instantiate later
# (the library exposes coinbase.rest.RESTClient in installed package)
try:
    import coinbase  # top-level package installed by coinbase-advanced-py
    from coinbase.rest import RESTClient
    print("✅ coinbase package imported (will try RESTClient).")
except Exception as e:
    # still continue; later instantiation will show clearer errors
    print("⚠️ Could not import coinbase/RESTClient at module import time:", type(e).__name__, e)
# ---------- end env/import block ----------
