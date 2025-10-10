#!/bin/bash
set -e

# Upgrade pip and install all dependencies
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

# Run the bot
exec python3 nija_bot.py
