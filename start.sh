#!/bin/bash

# -------------------
# Activate virtualenv
# -------------------
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# -------------------
# Set environment variables (optional override)
# -------------------
export USE_MOCK=False
export PORT=${PORT:-10000}  # Render provides $PORT automatically
echo "🔑 Using live API mode: USE_MOCK=$USE_MOCK"

# -------------------
# Run Flask API in background
# -------------------
echo "🚀 Starting nija_bot.py (Flask API)..."
nohup python nija_bot.py > logs/nija_bot.log 2>&1 &

# -------------------
# Run trading worker
# -------------------
echo "📈 Starting trading_worker.py..."
nohup python trading_worker.py > logs/trading_worker.log 2>&1 &

# -------------------
# Confirm running
# -------------------
echo "✅ All processes launched. Logs:"
echo "   nija_bot: logs/nija_bot.log"
echo "   trading_worker: logs/trading_worker.log"
