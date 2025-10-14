#!/usr/bin/env bash
set -eo pipefail

# Activate virtualenv
source .venv/bin/activate

# Install dependencies (safe)
pip install --upgrade pip
pip install -r requirements.txt

# Run the bot
python3 nija_bot.py

#!/usr/bin/env bash
set -eo pipefail

# ------------------------------
# start.sh for Render deploy
# ------------------------------

VENV=".venv"
PY="$VENV/bin/python3"

# 1️⃣ Create virtual environment if it doesn't exist
if [ ! -d "$VENV" ]; then
    echo "🛠️ Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# 2️⃣ Activate virtual environment
echo "⚡ Activating virtual environment..."
source "$VENV/bin/activate"

# 3️⃣ Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# 4️⃣ Install dependencies
if [ -f requirements.txt ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# 5️⃣ Run nija_bot.py
echo "🚀 Starting Nija Trading Bot..."
exec "$PY" nija_bot.py
