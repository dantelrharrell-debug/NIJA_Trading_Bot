import os
import coinbase as cb  # correct import for coinbase-advanced-py

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
