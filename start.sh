#!/bin/bash
set -e  # exit on any error

echo "🚀 Starting bot..."

# 1️⃣ Activate virtual environment
source .venv/bin/activate

# 2️⃣ Verify coinbase_advanced_py is available
python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py is available')"

# 3️⃣ Run your bot
python nija_bot.py
