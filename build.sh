#!/bin/sh
set -euo pipefail

# create venv (idempotent)
python3 -m venv .venv

# ensure pip exists in the venv
.venv/bin/python -m ensurepip --upgrade

# upgrade packaging tools inside the venv
.venv/bin/pip install --upgrade pip setuptools wheel

# install requirements into the venv
.venv/bin/pip install -r requirements.txt

# debug: show which python and which pip we're using (optional but helpful)
.venv/bin/python -c "import sys; print('VENV PYTHON:', sys.executable); import pkgutil; print('coinbase module spec:', pkgutil.find_loader('coinbase_advanced_py'))"

# final: run the app with the venv python
.venv/bin/python main.py
