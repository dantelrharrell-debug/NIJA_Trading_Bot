#!/bin/bash
set -euo pipefail

# 1) Upgrade basics (use --break-system-packages if Render environment complains)
python3 -m pip install --upgrade pip setuptools wheel

# 2) Install requirements into the environment Render provides
# Add --break-system-packages if your build environment enforces system package management
python3 -m pip install --break-system-packages -r requirements.txt

# 3) Start the bot with the same python that installed packages
exec python3 nija_bot.py
