#!/bin/bash
set -e  # Exit immediately if a command fails

echo "🛠 Cleaning previous virtual environment..."
rm -rf .venv

echo "🛠 Creating new virtual environment..."
python3 -m venv .venv

echo "🛠 Activating virtual environment..."
source .venv/bin/activate

echo "🛠 Upgrading pip..."
python3 -m pip install --upgrade pip

echo "🛠 Installing required packages..."
python3 -m pip install -r requirements.txt

echo "✅ Build complete!"
