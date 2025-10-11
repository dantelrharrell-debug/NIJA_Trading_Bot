import os
import base64
import tempfile
from coinbase.rest import RESTClient

# --- Load PEM from environment ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if not API_PEM_B64:
    print("❌ Environment variable API_PEM_B64 not set")
else:
    try:
        # 1. Clean base64: remove whitespace/newlines
        API_PEM_B64_clean = ''.join(API_PEM_B64.strip().split())
        
        # 2. Pad base64 to multiple of 4 if necessary
        missing_padding = len(API_PEM_B64_clean) % 4
        if missing_padding != 0:
            API_PEM_B64_clean += '=' * (4 - missing_padding)
        
        # 3. Decode to bytes (never UTF-8!)
        API_PEM_BYTES = base64.b64decode(API_PEM_B64_clean)
        
        # 4. Write bytes to temporary PEM file
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM_BYTES)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print(f"✅ Wrote PEM to {pem_temp_path}")
        
    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)

# --- Start Coinbase REST client ---
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
