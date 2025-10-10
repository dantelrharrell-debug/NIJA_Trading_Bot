#!/bin/bash
set -e

# Upgrade pip safely in the current environment
python3 -m pip install --upgrade pip setuptools wheel

# Force install the Coinbase package (in Render’s environment)
python3 -m pip install --no-cache-dir coinbase-advanced-py==1.8.2

# Install any other dependencies
python3 -m pip install --no-cache-dir -r requirements.txt

# Run the bot
exec python3 nija_bot.py
