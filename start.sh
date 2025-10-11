#!/bin/bash
set -e

# Upgrade pip
python3 -m pip install --upgrade pip

# Install coinbase-advanced-py
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

# Install remaining requirements
python3 -m pip install -r requirements.txt
#!/bin/bash
# exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting build..."

# Upgrade pip first
echo "🔹 Upgrading pip..."
python3 -m pip install --upgrade pip

# Force reinstall coinbase-advanced-py
echo "🔹 Installing coinbase-advanced-py..."
python3 -m pip install --force-reinstall coinbase-advanced-py==1.8.2

# Install all other dependencies
echo "🔹 Installing other requirements..."
python3 -m pip install -r requirements.txt

echo "✅ All dependencies installed successfully!"
