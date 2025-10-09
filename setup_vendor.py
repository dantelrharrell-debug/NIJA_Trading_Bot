#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
MODULE_NAME = "coinbase_advanced_py"
PACKAGE_VERSION = "1.8.2"

os.makedirs(VENDOR_DIR, exist_ok=True)

# 1️⃣ Download and install the package directly into vendor folder
print(f"📦 Installing {MODULE_NAME}=={PACKAGE_VERSION} into {VENDOR_DIR}...")

subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    f"{MODULE_NAME}=={PACKAGE_VERSION}",
    "--target", VENDOR_DIR,
    "--no-cache-dir",
    "--upgrade"
])

# 2️⃣ Verify it works
sys.path.insert(0, VENDOR_DIR)
try:
    mod = __import__(MODULE_NAME)
    print(f"✅ {MODULE_NAME} imported successfully, version: {getattr(mod, '__version__', 'unknown')}")
except ModuleNotFoundError:
    print(f"❌ Failed to import {MODULE_NAME} from {VENDOR_DIR}")
    sys.exit(1)
