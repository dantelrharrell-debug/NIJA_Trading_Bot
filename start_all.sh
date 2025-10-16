#!/bin/bash
# Activate virtual environment
. .venv/bin/activate

# Start nija_bot.py (Flask/Gunicorn) in background
echo "🚀 Starting nija_bot.py..."
gunicorn -b 0.0.0.0:$PORT nija_bot:app &

# Start trading_worker.py in background
echo "💹 Starting trading_worker.py..."
python trading_worker.py &

# Keep the script alive while both processes run
wait
