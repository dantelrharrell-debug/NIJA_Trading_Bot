#!/bin/bash
set -e  # exit on any error

# 1️⃣ Activate virtual environment
source .venv/bin/activate

# 2️⃣ Verify package installation
python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py is available')"

# 3️⃣ Run the bot
python nija_bot.py
