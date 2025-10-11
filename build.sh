#!/usr/bin/env bash
set -euo pipefail
echo "🛠️  build.sh (user-site install) starting..."

# ensure user-site bin is on PATH for any scripts installed by pip
export PATH="$HOME/.local/bin:$PATH"

# upgrade pip for this Python
python3 -m pip install --upgrade --user pip setuptools wheel

# install requirements into user site-packages
python3 -m pip install --user -r requirements.txt

# install coinbase explicitly (harmless if already installed)
python3 -m pip install --user coinbase-advanced-py==1.8.2

# quick sanity check
python3 -c "import sys, site; print('python', sys.executable); import coinbase_advanced_py; print('✅ coinbase_advanced_py import ok')"

echo "🛠️  build.sh finished"
