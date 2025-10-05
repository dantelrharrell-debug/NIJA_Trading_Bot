#!/bin/bash
set -e

echo "==> Creating virtual environment..."
python3 -m venv .venv

echo "==> Activating virtual environment..."
source .venv/bin/activate

echo "==> Upgrading pip..."
python3 -m pip install --upgrade pip

echo "==> Installing dependencies..."
python3 -m pip install -r requirements.txt
python3 -m pip install coinbase-advanced-py==1.8.2

echo "==> Starting bot..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
