#!/bin/bash
set -e

# -------------------------------------------------
# Create virtualenv if it doesn't exist
# -------------------------------------------------
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtualenv
source .venv/bin/activate

# Upgrade pip and install packages
pip install --upgrade pip setuptools wheel

# Reinstall coinbase_advanced_py to avoid caching issues
pip uninstall -y coinbase-advanced-py || true
pip install --no-cache-dir coinbase-advanced-py==1.8.2

# Install Flask (if not already)
pip install --upgrade Flask python-dotenv
