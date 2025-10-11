import os
import base64
import tempfile
from coinbase.rest import RESTClient

# Decode base64 PEM from env var
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        API_PEM = base64.b64decode(API_PEM_B64).decode("utf-8")
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w")
        tf.write(API_PEM)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ PEM written to temp file:", pem_temp_path)
    except Exception as e:
        raise SystemExit(f"❌ Failed to decode/write PEM: {e}")
else:
    raise SystemExit("❌ API_PEM_B64 not set in environment")

# Initialize Coinbase client using PEM file
client = RESTClient(key_file=pem_temp_path)

# Quick test
print(client.get_accounts())
