#!/bin/bash
echo "PWD: $(pwd)"
echo "Listing files:"
ls -la
echo "Starting Flask app..."
exec gunicorn main:app --bind 0.0.0.0:$PORT --workers 3
