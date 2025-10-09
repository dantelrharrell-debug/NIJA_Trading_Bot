#!/bin/bash
# ==========================
# build.sh
# ==========================
# Ensure we are in the correct directory
echo "📦 Starting build process..."

# Upgrade pip in the virtual environment
python3 -m pip install --upgrade pip

# Install all dependencies from requirements.txt
python3 -m pip install -r requirements.txt

echo "✅ Build complete."
