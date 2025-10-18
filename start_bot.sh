#!/bin/bash
echo '🌟 Activating virtual environment...'
source .venv/bin/activate || { echo '❌ Failed to activate venv'; exit 1; }
echo '✅ Virtual environment activated.'
echo '🌟 Installing dependencies inside venv...'
pip install --upgrade pip
pip install -r requirements.txt
echo '🌟 Running trading_worker_live.py...'
exec python trading_worker_live.py 2>&1 | tee render_bot.log
