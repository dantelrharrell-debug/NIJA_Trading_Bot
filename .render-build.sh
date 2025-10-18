#!/usr/bin/env bash
set -e

echo "🚀 Starting Render build for NIJA Bot..."

# 1️⃣ Activate virtual environment (create if missing)
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2️⃣ Upgrade pip inside the venv
pip install --upgrade pip

# 3️⃣ Install all dependencies from requirements.txt
# (force reinstall to avoid caching issues)
pip install --no-cache-dir -r requirements.txt

echo "✅ Dependencies installed."

# 4️⃣ Optional: Verify coinbase-advanced-py import
python -c "import coinbase_advanced_py as cb; print('✅ coinbase_advanced_py import OK')"

echo "✅ Build finished. Ready for deployment."
