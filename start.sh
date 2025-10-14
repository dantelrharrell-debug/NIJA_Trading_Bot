#!/bin/bash

echo "🔹 Activating virtual environment..."
source /opt/render/project/src/.venv/bin/activate

# Confirm Python executable
echo "Python executable: $(which python3)"

# Check if coinbase_advanced_py is available
python3 - <<'END'
import os

try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py loaded")
    os.environ["USE_MOCK"] = "False"
except ImportError:
    print("❌ coinbase_advanced_py not found. Running in mock mode.")
    os.environ["USE_MOCK"] = "True"
END

# Start the bot
python3 nija_bot.py
