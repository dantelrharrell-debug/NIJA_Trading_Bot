#!/bin/bash

# Activate virtual environment
source /opt/render/project/src/.venv/bin/activate

# Run the bot with the same Python
python3 nija_bot.py

#!/bin/bash

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
# 2. Upgrade pip & install dependencies
# ----------------------
pip install --upgrade pip
pip install -r requirements.txt

# ----------------------
# 3. Ensure Python is using the venv
# ----------------------
echo "🟢 Python executable being used: $(which python3)"
echo "🟢 Pip executable being used: $(which pip)"

# ----------------------
# 4. Run the bot
# ----------------------
python3 nija_bot.py
