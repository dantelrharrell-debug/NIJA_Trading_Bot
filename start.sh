#!/bin/bash
set -euo pipefail

# create venv (Render often already sets one; this is safe)
python3 -m venv .venv || true
. .venv/bin/activate

# upgrade pip and install requirements
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Export PORT for Flask (Render gives $PORT env var)
export PORT=${PORT:-10000}

# run bot (keeps using the same command you used before)
python3 nija_bot.py
