#!/bin/bash
echo "Starting NIJA Trading Bot..."
# Run uvicorn and log everything to a file
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &> debug.log || true
echo "Uvicorn exited. Last 50 lines of debug.log:"
tail -n 50 debug.log
