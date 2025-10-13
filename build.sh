#!/bin/bash
# ----------------------------
# Render Build Script for NIJA Trading Bot
# ----------------------------

set -e  # Exit immediately if a command fails

echo "🚀 Starting build..."

# 1. Create virtual environment
python3 -m venv .venv
echo "✅ Virtual environment created"

# 2. Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# 3. Ensure pip is installed and upgraded
python -m ensurepip --upgrade
pip install --upgrade pip
echo "✅ pip upgraded"

# 4. Install requirements
pip install -r requirements.txt
echo "✅ Requirements installed"

# 5. Optional: check that coinbase_advanced_py is installed
python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py imported successfully!')"

# 6. Run the bot
python main.py
echo "🚀 Bot started successfully"
