#!/bin/bash

# Use Render's $PORT if defined, otherwise default to 5000
PORT_NUMBER=${PORT:-5000}

exec gunicorn main:app --bind 0.0.0.0:$PORT_NUMBER --workers 3
