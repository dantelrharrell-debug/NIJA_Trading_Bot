#!/bin/bash
# start.sh

echo "==> Activating virtual environment"
source .venv/bin/activate

echo "==> Running bot"
python3 nija_bot.py

#!/usr/bin/env bash
set -euo pipefail

# start.sh - Render start script
# This script:
#  - ensures a .venv exists
#  - activates the venv
#  - upgrades pip and installs requirements
#  - runs nija_bot.py (exec so container PID 1 is Python process)

VENV_DIR=".venv"
PYTHON_BIN="${VENV_DIR}/bin/python3"
PIP_BIN="${VENV_DIR}/bin/pip"

echo "==> Start script executing"

if [ ! -d "${VENV_DIR}" ]; then
  echo "==> Creating virtualenv in ${VENV_DIR}"
  python3 -m venv "${VENV_DIR}"
fi

# Activate virtualenv
# shellcheck source=/dev/null
. "${VENV_DIR}/bin/activate"

echo "✅ Virtual environment activated."

echo "==> Upgrading pip"
"${PYTHON_BIN}" -m pip install --upgrade pip setuptools wheel

if [ -f requirements.txt ]; then
  echo "==> Installing requirements from requirements.txt"
  # Use --no-cache-dir to reduce disk use on free tiers
  "${PIP_BIN}" install --no-cache-dir -r requirements.txt
else
  echo "⚠️ requirements.txt not found - skipping pip install"
fi

echo "==> Running nija_bot.py"
# Exec so python becomes PID1 (Render expects your process to run in foreground)
exec "${PYTHON_BIN}" nija_bot.py
