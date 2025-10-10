#!/usr/bin/env bash
set -euo pipefail

# ensure pip, then install requirements in the active python
python3 -m pip install --upgrade pip setuptools wheel || true
python3 -m pip install -r requirements.txt

# Run the bot (Render will pass PORT environment variable automatically)
exec python3 nija_bot.py
