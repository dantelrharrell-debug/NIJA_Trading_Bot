#!/bin/bash
set -e

# Upgrade pip, setuptools, and wheel
python3 -m pip install --upgrade pip setuptools wheel

# Install dependencies
python3 -m pip install -r requirements.txt

# Run your bot
exec python3 nija_bot.py
