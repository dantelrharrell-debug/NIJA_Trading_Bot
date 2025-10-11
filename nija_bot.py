import os
import base64
import tempfile
from coinbase.rest import RESTClient

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Clean up any spaces or newlines in the base64 string
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())

        # Add missing padding if needed
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode base64 to bytes (DO NOT decode to UTF-8)
        API_PEM_BYTES = base64.b64decode(API_PEM_B64_clean)

        # Write bytes to a temporary PEM file
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
        # Pass the PEM file path to the REST client
        client = RESTClient(key_file=pem_temp_path)

        # Test connection by fetching accounts
        accounts = client.get_accounts()
        print("✅ Coinbase client started successfully!")
        print(accounts)
    except Exception as e:
        print("❌ Failed to start Coinbase client:", e)
else:
    print("❌ PEM file not available, cannot start client")
