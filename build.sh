#!/bin/bash
set -e
echo "🛠️  build.sh starting..."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# use explicit venv python for all installs
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

# quick verify import inside venv
echo "🔎 verifying coinbase import inside venv..."
./.venv/bin/python -c "import importlib, sys; print('python:', sys.executable); print('sys.path[0..3]=', sys.path[:4]); spec=importlib.util.find_spec('coinbase'); print('coinbase spec=', spec); import coinbase.rest as r; print('coinbase.rest ok ->', getattr(r,'__file__',None))"
echo "✅ build.sh finished."
