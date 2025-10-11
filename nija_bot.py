import os
import base64
import tempfile
from coinbase.rest import RESTClient

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Clean up the string: remove spaces/newlines
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())
        # Pad to multiple of 4
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode to bytes
        pem_bytes = base64.b64decode(API_PEM_B64_clean)

        # Check if this is already ASCII PEM (starts with "-----")
        if pem_bytes.startswith(b"-----"):
            mode = "w"  # ASCII text
            pem_content = pem_bytes.decode("utf-8")
        else:
            mode = "wb"  # Binary DER
            pem_content = pem_bytes

        # Write temp PEM file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode=mode)
        tf.write(pem_content)
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

if pem_temp_path:
    with open(pem_temp_path, "rb") as f:
        print("✅ PEM file content preview:", f.read(64), "...")
