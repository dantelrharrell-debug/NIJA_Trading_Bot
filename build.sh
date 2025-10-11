#!/bin/bash
set -e  # exit on any error

echo "🚀 Starting build..."

# 1️⃣ Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 2️⃣ Upgrade pip inside virtual environment
echo "🔧 Upgrading pip..."
./.venv/bin/python -m pip install --upgrade pip

# 3️⃣ Install dependencies from requirements.txt
echo "📦 Installing requirements..."
./.venv/bin/python -m pip install -r requirements.txt

# 4️⃣ Explicitly install Coinbase library
echo "💰 Installing coinbase-advanced-py..."
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

# 5️⃣ Verify package installation
echo "✅ Verifying coinbase-advanced-py..."
./.venv/bin/python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py is installed!')"

echo "🎉 Build finished successfully!"
