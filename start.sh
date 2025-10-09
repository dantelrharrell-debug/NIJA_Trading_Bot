#!/bin/bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Install all dependencies
python3 -m pip install -r requirements.txt

# Run the bot
python3 -u nija_bot.py
