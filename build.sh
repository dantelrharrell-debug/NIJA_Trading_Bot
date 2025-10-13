#!/bin/sh

# Create virtual environment
python3 -m venv .venv || exit 1
.venv/bin/python -m ensurepip --upgrade || exit 1
.venv/bin/pip install --upgrade pip || exit 1
.venv/bin/pip install -r requirements.txt || exit 1

# Run the bot
.venv/bin/python main.py
