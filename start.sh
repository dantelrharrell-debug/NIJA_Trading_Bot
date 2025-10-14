#!/bin/bash

# ------------------ activate virtual environment ------------------
echo "==> Activating virtual environment"
source .venv/bin/activate
echo "✅ Virtual environment activated."

# ------------------ upgrade pip & setuptools ------------------
echo "==> Upgrading pip and setuptools"
pip install --upgrade pip setuptools wheel

# ------------------ install requirements ------------------
echo "==> Installing requirements"
pip install -r requirements.txt

# ------------------ run the bot ------------------
echo "==> Running nija_bot.py"
python3 nija_bot.py
