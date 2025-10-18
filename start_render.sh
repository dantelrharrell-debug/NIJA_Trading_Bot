#!/bin/bash
# start_render.sh
# Render deployment helper for both web service and trading worker
# Includes debug to verify coinbase_advanced_py

# 1. Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    . .venv/bin/activate
else
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 2. Install/Force reinstall coinbase-advanced-py to ensure import works
pip install --upgrade --force-reinstall coinbase-advanced-py==1.8.2

# 3. Debug: Confirm coinbase_advanced_py import
echo "🔍 Verifying coinbase_advanced_py..."
python - <<END
import sys
try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py import successful")
    print("Python executable:", sys.executable)
    print("Python path:", sys.path)
except Exception as e:
    print("❌ coinbase_advanced_py import FAILED:", e)
    sys.exit(1)
END

# 4. Decide mode: Web or Worker
MODE=${1:-web}  # Default to web if no argument

if [ "$MODE" == "web" ]; then
    echo "Starting web service..."
    exec gunicorn -b 0.0.0.0:$PORT nija_bot:app
elif [ "$MODE" == "worker" ]; then
    echo "Starting trading worker..."
    exec python trading_worker_live.py
else
    echo "❌ Unknown mode: $MODE"
    exit 1
fi
