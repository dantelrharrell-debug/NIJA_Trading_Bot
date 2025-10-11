#!/bin/bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install dependencies
python3 -m pip install --no-cache-dir -r requirements.txt

# Run your bot
python3 nija_bot.py
