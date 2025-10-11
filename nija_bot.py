import os
import base64
import tempfile
from coinbase.rest import RESTClient

# Get your base64 PEM string from environment variable
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Fix missing padding if needed
        missing_padding = len(API_PEM_B64) % 4
        if missing_padding:
            API_PEM_B64 += '=' * (4 - missing_padding)

        # Decode the base64 string to PEM
        API_PEM = base64.b64decode(API_PEM_B64).decode("utf-8")

        # Write PEM to a temporary file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w")
        tf.write(API_PEM)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote PEM to", pem_temp_path)

    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)
        raise SystemExit(1)
else:
    print("❌ API_PEM_B64 environment variable not set")
    raise SystemExit(1)

# Initialize Coinbase client using PEM file
client = RESTClient(key_file=pem_temp_path)

# Quick test to check connection
try:
    accounts = client.get_accounts()
    print("✅ Coinbase accounts retrieved:", accounts)
except Exception as e:
    print("❌ Coinbase API connection failed:", e)
