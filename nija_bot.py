import os
import base64
import tempfile

try:
    from coinbase.rest import RESTClient
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase-advanced-py not installed. Check requirements.txt and build command.")

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # Remove whitespace/newlines
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)

        # Decode to bytes (binary, no UTF-8)
        API_PEM_BYTES = base64.b64decode(API_PEM_B64_clean)

        # Save to temp PEM file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb") as tf:
            tf.write(API_PEM_BYTES)
            pem_temp_path = tf.name
        print("✅ PEM written to", pem_temp_path)
    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)

# --- Coinbase Client ---
if pem_temp_path:
    try:
        client = RESTClient(key_file=pem_temp_path)
        accounts = client.get_accounts()
        print("✅ Coinbase client started!")
        print(accounts)
    except Exception as e:
        print("❌ Failed to start Coinbase client:", e)
else:
    print("❌ PEM not available. Cannot start client.")
