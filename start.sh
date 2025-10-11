#!/bin/bash
set -e

echo "🚀 Starting build..."

echo "🔹 Upgrading pip..."
python3 -m pip install --upgrade pip

echo "🔹 Ensuring coinbase-advanced-py is installed..."
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

echo "🔹 Installing other requirements from requirements.txt..."
python3 -m pip install -r requirements.txt

echo "✅ All dependencies installed successfully!"
