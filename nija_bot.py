import os
import base64
import tempfile
from coinbase.rest import RESTClient

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Remove whitespace/newlines just in case
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())

        # Auto-pad the string if missing '=' at the end
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode the base64
        API_PEM = base64.b64decode(API_PEM_B64_clean).decode("utf-8")

        # Write to a temporary PEM file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w")
        tf.write(API_PEM)
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
