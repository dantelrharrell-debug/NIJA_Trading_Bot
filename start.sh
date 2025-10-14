#!/usr/bin/env bash
set -euo pipefail

# Activate venv
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

# Prefer dashboard env var; if not set, explicitly default to False
: "${USE_MOCK:=False}"
export USE_MOCK

echo "🔎 Debug: checking coinbase import candidates"
python3 -c "import importlib, sys, pkgutil, json; names=['coinbase_advanced_py','coinbase_advanced','coinbase','coinbase_advanced_py_client']; found=[]; \
for n in names: found.append({'name':n, 'spec': bool(importlib.util.find_spec(n))}); \
print(json.dumps(found)); \
print('--- installed top-level modules containing coinbase ---'); \
print('\\n'.join([m.name for m in pkgutil.iter_modules() if 'coinbase' in m.name.lower()]))"

echo "🔹 Python executable: $(which python3)"
echo "🔹 Starting NIJA Bot (USE_MOCK=${USE_MOCK})"
exec python3 nija_bot.py
