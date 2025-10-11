#!/bin/bash
set -e

echo "🔧 build.sh starting..."

# 1) create virtual env if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# 2) use venv's python for all installs (no relying on "activate" side-effects)
./.venv/bin/python -m pip install --upgrade pip

# 3) install requirements + explicit coinbase package (explicit is safe)
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

# 4) sanity check: try importing package using venv python
echo "🔎 Verifying coinbase package inside venv..."
./.venv/bin/python -c "from coinbase.rest import RESTClient; print('✅ coinbase-advanced-py import ok')"

echo "✅ build.sh finished."
