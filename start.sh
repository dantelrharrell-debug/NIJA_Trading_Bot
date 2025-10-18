#!/bin/bash
# =========================
# Railway deployment startup
# =========================

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Upgrade pip to avoid version conflicts
pip install --upgrade pip

# Reinstall dependencies
pip install --no-cache-dir -r requirements.txt

# Start your bot with Gunicorn
exec gunicorn -b 0.0.0.0:$PORT main:app
