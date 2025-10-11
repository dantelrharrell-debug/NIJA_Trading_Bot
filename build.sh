#!/bin/bash
set -e

echo "🔧 build.sh starting..."

# 1) create virtualenv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# 2) use venv's python for all installs (explicit path avoids activation issues)
./.venv/bin/python -m pip install --upgrade pip

# 3) install requirements + coinbase package explicitly
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

# 4) quick verification inside venv
echo "🔎 Verifying coinbase package inside venv..."
./.venv/bin/python -c "from coinbase.rest import RESTClient; print('✅ coinbase-advanced-py import ok')"

echo "✅ build.sh finished."
