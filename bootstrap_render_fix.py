"""
Render Bootstrap Fix
--------------------
This file ensures 'coinbase_advanced_py' is available at runtime even if Render’s build cache drops it.
It will auto-install the package once inside the running container (not during build).
This does NOT affect Railway or local environments.
"""

import os
import sys
import subprocess
import importlib

PKG = "coinbase_advanced_py"

def ensure_package(pkg: str):
    try:
        importlib.import_module(pkg)
        print(f"✅ {pkg} already available.")
    except ModuleNotFoundError:
        print(f"⚠️  {pkg} not found — attempting runtime install...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--no-cache-dir", "--upgrade"])
        print(f"✅ {pkg} installed successfully.")
        importlib.import_module(pkg)
        print(f"✅ {pkg} import verified.")

# Only run on Render (detected via environment)
if os.getenv("RENDER") or "render" in os.getenv("HOSTNAME", "").lower():
    ensure_package(PKG)
else:
    print("🌍 Not running on Render — skipping bootstrap fix.")
