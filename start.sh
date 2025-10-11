#!/bin/bash
set -e

echo "🚀 Starting build..."

# Upgrade pip
python3 -m pip install --upgrade pip

# Force reinstall coinbase-advanced-py
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

# Install other requirements
python3 -m pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"
