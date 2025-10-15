#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting build for NIJA Bot..."

# 1️⃣ Create virtualenv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtualenv created"
fi

# 2️⃣ Activate virtualenv
source .venv/bin/activate

# 3️⃣ Upgrade pip
pip install --upgrade pip

# 4️⃣ Install dependencies
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
    echo "✅ Dependencies installed from requirements.txt"
fi

# 5️⃣ Reinstall coinbase-advanced-py to avoid import issues
pip uninstall -y coinbase-advanced-py || true
pip install --no-cache-dir coinbase-advanced-py==1.8.2
echo "✅ coinbase-advanced-py installed"

echo "🚀 Build completed!"
