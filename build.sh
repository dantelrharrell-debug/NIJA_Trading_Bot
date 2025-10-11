# Verify installation
./.venv/bin/python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py installed correctly')"
#!/bin/bash
set -e  # Exit on any error

# 1️⃣ Create virtual environment (if it doesn't exist)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 2️⃣ Upgrade pip inside the virtual environment
./.venv/bin/python -m pip install --upgrade pip

# 3️⃣ Install all requirements from requirements.txt
./.venv/bin/python -m pip install -r requirements.txt

# 4️⃣ Explicitly install Coinbase library
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

echo "✅ Build finished successfully"
