#!/usr/bin/env bash
set -e

# 1️⃣ Create virtual environment
python3 -m venv .venv

# 2️⃣ Activate it
source .venv/bin/activate

# 3️⃣ Upgrade pip
pip install --upgrade pip

# 4️⃣ Install coinbase_advanced_py
pip install --no-cache-dir coinbase-advanced-py==1.8.2

# 5️⃣ Install all other requirements using wheels only
pip install --no-cache-dir -r requirements.txt --only-binary=:all:
