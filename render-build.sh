#!/usr/bin/env bash
set -e

# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install coinbase_advanced_py
pip install --no-cache-dir coinbase-advanced-py==1.8.2

# 4. Install all requirements with prebuilt wheels only
pip install --no-cache-dir -r requirements.txt --only-binary=:all:
