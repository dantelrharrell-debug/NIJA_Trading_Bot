#!/bin/bash
set -euo pipefail
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt
exec python3 nija_bot.py
