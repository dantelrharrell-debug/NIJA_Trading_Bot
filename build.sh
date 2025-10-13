#!/bin/sh
python3 -m venv .venv
.venv/bin/python -m ensurepip --upgrade
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
