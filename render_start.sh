#!/bin/bash
# start.sh - Render deployment entry
# Supports both web service and worker
# Ensures coinbase_advanced_py is installed and importable

# --- 1. Activate venv ---
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    . .venv/bin/activate
else
    echo "❌ Virtual environment missing. Creating..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# --- 2. Force reinstall coinbase-advanced-py ---
pip install --upgrade --force-reinstall coinbase-advanced-py==1.8.2

# --- 3. Verify import ---
echo "🔍 Checking coinbase_advanced_py..."
python - <<END
import sys
try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py imported successfully")
    print("Python executable:", sys.executable)
    print("sys.path:", sys.path)
except Exception as e:
    print("❌ coinbase_advanced_py import FAILED:", e)
    sys.exit(1)
END

# --- 4. Launch mode ---
MODE=${1:-web}  # Default to web

if [ "$MODE" == "web" ]; then
    echo "🚀 Starting web service..."
    exec gunicorn -b 0.0.0.0:$PORT nija_bot:app
elif [ "$MODE" == "worker" ]; then
    echo "🤖 Starting trading worker..."
    exec python trading_worker_live.py
else
    echo "❌ Unknown mode: $MODE"
    exit 1
fi
