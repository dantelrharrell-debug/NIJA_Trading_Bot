#!/bin/bash
set -e

# Upgrade pip
python3 -m pip install --upgrade pip

# Reinstall Coinbase library
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

# Install all other requirements
python3 -m pip install -r requirements.txt
