#!/bin/bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install dependencies
python3 -m pip install --no-cache-dir -r requirements.txt

# Run bot
python3 nija_bot.py

#!/bin/bash
pip install --upgrade pip
pip install --force-reinstall coinbase-advanced-py==1.8.2
pip install -r requirements.txt
