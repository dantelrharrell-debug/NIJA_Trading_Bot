#!/bin/bash
# start.sh — only install deps and run bot

# Upgrade pip safely (break-system-packages because of Render)
python3 -m pip install --break-system-packages --upgrade pip

# Install dependencies if not already installed
python3 -m pip install --break-system-packages -r requirements.txt

# Start the bot
python3 nija_bot.py
