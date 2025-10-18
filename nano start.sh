#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Start Gunicorn with your Flask app
exec gunicorn main:app --bind 0.0.0.0:$PORT --workers 3
