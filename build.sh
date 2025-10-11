#!/usr/bin/env bash
set -euo pipefail

echo "🚀 build.sh: creating virtualenv and installing dependencies..."

# create a venv inside the repo
python3 -m venv .venv

# use the venv pip to install packages
. .venv/bin/activate

echo "🔹 Upgrading pip inside venv..."
python -m pip install --upgrade pip

echo "🔹 Ensuring coinbase-advanced-py pinned version..."
python -m pip install --force-reinstall coinbase-advanced-py==1.8.2

echo "🔹 Installing requirements.txt..."
if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt
fi

echo "✅ build.sh finished. venv ready at .venv/"
