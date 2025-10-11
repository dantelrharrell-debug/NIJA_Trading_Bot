#!/bin/bash
# upgrade pip
python3 -m pip install --upgrade pip

# install dependencies
python3 -m pip install --no-cache-dir -r requirements.txt

# run the bot
python3 nija_bot.py
