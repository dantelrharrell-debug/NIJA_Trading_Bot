#!/usr/bin/env bash
# start.sh - start the Nija Flask app (no tests, no imports that use request)
export FLASK_ENV=production
python main.py
#!/bin/bash
PORT=${PORT:-8080}
python3 main.py
