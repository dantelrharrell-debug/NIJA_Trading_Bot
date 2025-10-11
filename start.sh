#!/usr/bin/env bash
set -euo pipefail
echo "🚀 start.sh (system python + user-site) starting..."

# ensure user-site bin is on PATH
export PATH="$HOME/.local/bin:$PATH"

# run with system python (packages installed to ~/.local)
exec python3 nija_bot.py
