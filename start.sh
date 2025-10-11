#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Confirm that coinbase_advanced_py is installed
python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py is available')"

# Run your bot
python nija_bot.py
