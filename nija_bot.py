import os
import base64
import tempfile
from coinbase.rest import RESTClient

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Remove spaces/newlines
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())
        # Pad if length not multiple of 4
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode to bytes ONLY
        API_PEM_BYTES = base64.b64decode(API_PEM_B64_clean)

        # Write bytes to temp PEM file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM_BYTES)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote PEM to", pem_temp_path)
    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)

# --- Coinbase REST Client ---
if pem_temp_path:
    try:
        client = RESTClient(key_file=pem_temp_path)
        accounts = client.get_accounts()
        print("✅ Coinbase client started successfully!")
        print(accounts)
    except Exception as e:
        print("❌ Failed to start Coinbase client:", e)
else:
    print("❌ PEM file not available, cannot start client")
