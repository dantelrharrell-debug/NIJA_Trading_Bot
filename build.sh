#!/bin/bash
set -e  # Exit on error

# ------------------------
# Check if venv exists and rebuild if missing or corrupted
# ------------------------
if [ ! -d ".venv" ]; then
    echo "🛠 .venv missing. Creating virtual environment..."
else
    echo "🛠 .venv exists. Checking for coinbase_advanced_py..."
    . .venv/bin/activate
    if ! python3 -c "import coinbase_advanced_py" &> /dev/null; then
        echo "⚠️ coinbase_advanced_py not found in .venv. Rebuilding..."
        rm -rf .venv
    fi
    deactivate
fi

# ------------------------
# Create venv
# ------------------------
echo "🛠 Creating virtual environment..."
python3 -m venv .venv

echo "🛠 Activating virtual environment..."
source .venv/bin/activate

echo "🛠 Upgrading pip..."
python3 -m pip install --upgrade pip

echo "🛠 Installing required packages..."
python3 -m pip install -r requirements.txt

echo "✅ Build complete!"
