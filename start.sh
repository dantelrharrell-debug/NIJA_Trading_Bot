#!/bin/bash
source .venv/bin/activate  # activate virtualenv
python3 nija_bot.py        # run your bot

#!/bin/bash
# Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated."

# Install/ensure requirements
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Run bot
python3 nija_bot.py
