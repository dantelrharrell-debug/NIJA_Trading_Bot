#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting build..."

# Upgrade pip
echo "🔹 Upgrading pip..."
python3 -m pip install --upgrade pip

# Force reinstall coinbase-advanced-py
echo "🔹 Installing coinbase-advanced-py..."
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

# Install all other dependencies
echo "🔹 Installing other requirements..."
python3 -m pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"
