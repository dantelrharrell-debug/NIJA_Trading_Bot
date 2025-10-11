#!/bin/bash
# upgrade pip first
python3 -m pip install --upgrade pip

# install dependencies from requirements.txt
python3 -m pip install --no-cache-dir -r requirements.txt

# run your bot
python3 nija_bot.py
