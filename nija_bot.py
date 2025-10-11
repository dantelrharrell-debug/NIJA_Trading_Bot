import os, base64, tempfile
from coinbase.rest import RESTClient

# --- PEM Handling ---
API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

if API_PEM_B64:
    try:
        # auto-pad the string if missing '=' at the end
        missing_padding = len(API_PEM_B64) % 4
        if missing_padding != 0:
            API_PEM_B64 += '=' * (4 - missing_padding)
        
        API_PEM = base64.b64decode(API_PEM_B64).decode("utf-8")
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w")
        tf.write(API_PEM)
        tf.flush(); tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote PEM to", pem_temp_path)
    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)

# --- Coinbase REST Client ---
if pem_temp_path:
    client = RESTClient(key_file=pem_temp_path)
    print(client.get_accounts())  # quick test
else:
    print("❌ PEM file not available, cannot start client")
