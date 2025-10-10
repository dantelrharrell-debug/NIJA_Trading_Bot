#!/bin/bash
set -e

# Upgrade pip and install requirements in Render's environment
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

# Run the bot
exec python3 nija_bot.py
