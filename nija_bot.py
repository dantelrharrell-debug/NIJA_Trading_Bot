import os
import coinbase as cb  # correct import for coinbase-advanced-py
#!/bin/bash
set -euo pipefail

# -----------------------
# Activate virtualenv
# -----------------------
echo "🟢 Activating venv..."
source /opt/render/project/src/.venv/bin/activate

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

# -----------------------
# Install dependencies
# -----------------------
echo "🟢 Installing dependencies..."
$VENV_PY -m pip install --upgrade pip
$VENV_PIP install -r requirements.txt

# -----------------------
# Write PEM file from env
# -----------------------
PEM_PATH="/tmp/my_coinbase_key.pem"

if [[ -n "${COINBASE_PEM:-}" ]]; then
    echo "🟢 Writing PEM file..."
    echo "$COINBASE_PEM" > "$PEM_PATH"
    echo "✅ PEM written to $PEM_PATH"
else
    echo "⚠️ COINBASE_PEM not set. Bot will run with mock balances."
fi

# -----------------------
# Start the bot
# -----------------------
echo "🚀 Starting Nija Bot..."
$VENV_PY nija_bot.py

# -------------------------------
# Coinbase PEM / Live trading setup
# -------------------------------

# Path where PEM will be temporarily written
PEM_PATH = "/tmp/my_coinbase_key.pem"

# Fetch PEM content from environment variable
PEM_CONTENT = os.getenv("COINBASE_PEM")

if PEM_CONTENT:
    # Write PEM content to temporary file
    with open(PEM_PATH, "w") as f:
        f.write(PEM_CONTENT)
    print(f"✅ PEM written to {PEM_PATH}")

    try:
        # Initialize real Coinbase client
        client = cb.Client(api_key_path=PEM_PATH)
        LIVE_TRADING = True
        print("✅ Live Coinbase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Coinbase client: {e}")
        print("⚠️ Falling back to MockClient")
        from mock_client import MockClient  # your existing mock
        client = MockClient()
        LIVE_TRADING = False
else:
    # PEM not found → fallback to mock client
    print("⚠️ COINBASE_PEM not set, using MockClient")
    from mock_client import MockClient  # your existing mock
    client = MockClient()
    LIVE_TRADING = False

# -------------------------------
# Example: check balances
# -------------------------------
balances = client.get_account_balances()
print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")
