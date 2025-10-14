#!/bin/bash

# ---------- Activate virtual environment ----------
if [ -d ".venv" ]; then
    echo "🔹 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ Virtual environment not found, creating..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# ---------- Check that coinbase_advanced_py is installed ----------
python3 - <<END
import sys
import site

print("Python executable:", sys.executable)
print("Python sys.path:", sys.path)
print("Site-packages directories:", site.getsitepackages())

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py found")
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py NOT found")
END

# ---------- Start your bot ----------
echo "🚀 Launching Nija bot..."
python3 nija_bot.py
