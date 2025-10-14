#!/bin/bash
source .venv/bin/activate
python3 nija_bot.py

#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip just in case
python3 -m pip install --upgrade pip

# Install requirements (safe to run on each start)
python3 -m pip install -r requirements.txt

# Run the bot
python3 nija_bot.py
