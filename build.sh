#!/bin/bash
set -e  # Stop on any error

echo "==> Creating virtual environment..."
python3 -m venv .venv

echo "==> Activating virtual environment..."
source .venv/bin/activate

echo "==> Upgrading pip..."
python3 -m pip install --upgrade pip

echo "==> Installing requirements..."
python3 -m pip install -r requirements.txt

echo "==> Installing coinbase-advanced-py explicitly..."
python3 -m pip install coinbase-advanced-py==1.8.2

echo "✅ Build completed successfully!"
