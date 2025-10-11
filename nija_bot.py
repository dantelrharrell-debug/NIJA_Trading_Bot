import os
import sys
import base64
import tempfile

# Try Coinbase library imports
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not installed. Make sure build.sh installed dependencies correctly.")
    sys.exit(1)

# --- Load API keys from environment ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")  # Optional, only if you need PEM auth

pem_temp_path = None
client = None

# --- PEM Handling if API_PEM_B64 exists ---
if API_PEM_B64:
    try:
        # Remove whitespace and fix base64 padding
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode to bytes (do NOT decode as UTF-8)
        pem_bytes = base64.b64decode(API_PEM_B64_clean)

        # Write to temp PEM file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(pem_bytes)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print(f"✅ Wrote PEM to {pem_temp_path}")

    except Exception as e:
        print(f"❌ Failed to decode/write PEM: {e}")
        pem_temp_path = None

# --- Initialize Coinbase client ---
try:
    if pem_temp_path:
        client = cb.RESTClient(key_file=pem_temp_path)
    elif API_KEY and API_SECRET:
        client = cb.Client(API_KEY, API_SECRET)
    else:
        raise ValueError("No valid Coinbase credentials found. Set API_KEY/API_SECRET or API_PEM_B64")

    # Test: fetch accounts
    accounts = client.get_account_balances()
    print("✅ Coinbase client started successfully!")
    print(accounts)

except Exception as e:
    print(f"❌ Failed to start Coinbase client: {e}")
    sys.exit(1)

# --- Your trading bot logic starts here ---
print("🚀 NIJA bot is live and ready to trade!")

# Example: add more trading logic below
# client.buy('BTC', 0.01)
# client.sell('ETH', 0.01)
