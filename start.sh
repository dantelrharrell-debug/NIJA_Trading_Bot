#!/bin/bash

# Use Render's $PORT if defined, otherwise default to 5000 for local testing
PORT_NUMBER=${PORT:-5000}

# Start Gunicorn with your Flask app
exec gunicorn main:app --bind 0.0.0.0:$PORT_NUMBER --workers 3
