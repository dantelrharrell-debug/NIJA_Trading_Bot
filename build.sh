#!/bin/sh

# 1. Create virtual environment
python3 -m venv .venv
.venv/bin/python -m ensurepip --upgrade
.venv/bin/pip install --upgrade pip

# 2. Install requirements
.venv/bin/pip install -r requirements.txt

# 3. Start the bot
.venv/bin/python main.py
