#!/bin/bash
echo "🔹 Activating virtual environment..."
source /opt/render/project/src/.venv/bin/activate

# Confirm Python and module
python3 -c "import sys; print('Python:', sys.executable); import coinbase_advanced_py; print('✅ coinbase_advanced_py loaded')"

# Start the bot
python3 nija_bot.py

#!/bin/bash
# start.sh

echo "🔹 Activating virtual environment..."
export VIRTUAL_ENV="/opt/render/project/src/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"
source "$VIRTUAL_ENV/bin/activate"

echo "Python executable: $(which python3)"
echo "Python version: $(python3 --version)"
echo "Site-packages directory: $(python3 -c 'import site; print(site.getsitepackages())')"

# Double-check coinbase-advanced-py is installed
python3 -m pip show coinbase-advanced-py || pip install -r requirements.txt

# Launch bot
python3 nija_bot.py
