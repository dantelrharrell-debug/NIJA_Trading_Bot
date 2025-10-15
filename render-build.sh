#!/usr/bin/env bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir coinbase-advanced-py==1.8.2
pip install --no-cache-dir -r requirements.txt
