#!/bin/bash
set -e

# Upgrade pip/wheel/setuptools
python3 -m pip install --upgrade pip setuptools wheel

# Install dependencies
python3 -m pip install -r requirements.txt

# Run the bot
exec python3 nija_bot.py
