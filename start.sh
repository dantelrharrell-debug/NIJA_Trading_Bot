#!/bin/bash
# start.sh

# 1️⃣ Activate virtual environment
source .venv/bin/activate

# 2️⃣ Optional debug
echo "🟢 Python: $(which python)"
python -m pip show coinbase-advanced-py

# 3️⃣ Run bot explicitly with venv Python
.venv/bin/python nija_bot.py

#!/bin/bash
# start.sh

# ----------------------
# 1. Activate virtual environment
# ----------------------
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi

# ----------------------
# 2. Install dependencies only if missing
# ----------------------
REQUIRED_PKG="coinbase-advanced-py"
PKG_OK=$(python -m pip show $REQUIRED_PKG | grep Version)
if [ "" = "$PKG_OK" ]; then
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "✅ Dependencies already installed"
fi

# ----------------------
# 3. Debug info (optional)
# ----------------------
echo "🟢 Python executable being used: $(which python)"
echo "🟢 Pip executable being used: $(which pip)"
python -m pip show coinbase-advanced-py

# ----------------------
# 4. Run the bot
# ----------------------
python nija_bot.py
