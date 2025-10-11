#!/bin/bash
set -e

echo "🔹 Upgrading pip..."
python3 -m pip install --upgrade pip

echo "🔹 Installing coinbase-advanced-py..."
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

echo "🔹 Installing other requirements..."
python3 -m pip install -r requirements.txt

echo "✅ Build step finished. Starting bot..."
python3 nija_bot.py
