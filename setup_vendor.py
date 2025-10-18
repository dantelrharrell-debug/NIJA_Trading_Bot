#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

# Configuration
PACKAGE_NAME = "coinbase-advanced-py"
PACKAGE_VERSION = "1.8.2"
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
EXTRACT_DIR = os.path.join("/tmp", "coinbase_vendor")

# Create vendor and temp directories
os.makedirs(VENDOR_DIR, exist_ok=True)
shutil.rmtree(EXTRACT_DIR, ignore_errors=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

print(f"📦 Downloading {PACKAGE_NAME}=={PACKAGE_VERSION}...")
subprocess.check_call([
    sys.executable, "-m", "pip", "download",
    f"{PACKAGE_NAME}=={PACKAGE_VERSION}",
    "--no-deps", "-d", EXTRACT_DIR
])

# Find the wheel file
wheel_files = [f for f in os.listdir(EXTRACT_DIR) if f.endswith(".whl")]
if not wheel_files:
    sys.exit("❌ Could not find the wheel file!")

wheel_path = os.path.join(EXTRACT_DIR, wheel_files[0])
print(f"🛠 Extracting {wheel_path} to vendor folder...")

# Extract wheel
subprocess.check_call(["unzip", "-o", wheel_path, "-d", EXTRACT_DIR])

# Copy the package folder to vendor
package_folder_name = PACKAGE_NAME.replace("-", "_")
src_folder = os.path.join(EXTRACT_DIR, package_folder_name)
dst_folder = os.path.join(VENDOR_DIR, package_folder_name)

if os.path.exists(dst_folder):
    shutil.rmtree(dst_folder)
shutil.copytree(src_folder, dst_folder)

print(f"✅ {PACKAGE_NAME} has been vendored into {dst_folder}")
print("💡 You can now import it in nija_bot.py from vendor folder.")
