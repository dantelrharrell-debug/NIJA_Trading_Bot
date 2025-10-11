#!/bin/bash
set -e  # Exit immediately if any command fails

# 1️⃣ Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 2️⃣ Upgrade pip in the virtual environment
./.venv/bin/python -m pip install --upgrade pip

# 3️⃣ Install all requirements from requirements.txt
./.venv/bin/python -m pip install -r requirements.txt

# 4️⃣ Explicitly install Coinbase library
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

echo "✅ Build complete"
