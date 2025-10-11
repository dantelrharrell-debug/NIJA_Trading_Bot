#!/bin/bash
set -e

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2
