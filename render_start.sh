python --version
which python

#!/usr/bin/env bash
set -e  # stop on error

# 1️⃣ Activate your virtual environment
echo "Activating venv..."
. .venv/bin/activate

# 2️⃣ Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# 3️⃣ Force reinstall all requirements
echo "Installing dependencies..."
pip install --upgrade --force-reinstall -r requirements.txt

# 4️⃣ Verify coinbase_advanced_py is installed
echo "Checking coinbase_advanced_py..."
python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py loaded')"

# 5️⃣ Start Gunicorn with absolute venv path
echo "Starting Gunicorn..."
$PWD/.venv/bin/gunicorn -b 0.0.0.0:$PORT nija_bot:app
