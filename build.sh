#!/bin/bash
# build.sh

# Create virtualenv if it doesn't exist
python3 -m venv .venv

# Activate virtualenv
source .venv/bin/activate

# Upgrade pip just in case
pip install --upgrade pip

# Install all dependencies
pip install --no-cache-dir -r requirements.txt

# Reinstall coinbase-advanced-py to fix module detection
pip uninstall -y coinbase-advanced-py
pip install --no-cache-dir coinbase-advanced-py==1.8.2
