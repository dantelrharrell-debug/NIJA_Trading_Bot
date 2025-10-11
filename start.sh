#!/bin/bash
set -e

echo "🚀 Starting build..."

# Use python -m pip so options like --upgrade are interpreted by pip
echo "🔹 Upgrading pip..."
python3 -m pip install --upgrade pip

echo "🔹 Installing coinbase-advanced-py (specific version)..."
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

echo "🔹 Installing other requirements from requirements.txt..."
python3 -m pip install -r requirements.txt

echo "✅ All dependencies installed successfully!"
