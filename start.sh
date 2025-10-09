#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Starting Nija Trading Bot..."
# ensure vendor present; python file will attempt pip->vendor fallback if needed
python3 nija_bot.py
