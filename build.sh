#!/usr/bin/env bash
set -e  # Exit immediately if a command fails
set -o pipefail  # Catch errors in piped commands

# 1️⃣ Create virtual environment
python3 -m venv .venv

# 2️⃣ Activate virtual environment
source .venv/bin/activate

# 3️⃣ Upgrade pip, wheel, and setuptools
python -m ensurepip --upgrade
pip install --upgrade pip wheel setuptools

# 4️⃣ Install all requirements
pip install -r requirements.txt

# 5️⃣ Run the bot
python main.py
