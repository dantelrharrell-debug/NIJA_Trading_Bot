import os
import base64
import tempfile
from coinbase.rest import RESTClient

# 🔐 Load Coinbase credentials
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")

if not all([API_KEY, API_SECRET, API_PEM_B64]):
    raise SystemExit("❌ Missing API_KEY, API_SECRET, or API_PEM_B64")

# 🔓 Decode PEM key and write temporary file
def bytes_is_pem(b: bytes) -> bool:
    return b.startswith(b"-----BEGIN")

try:
    clean = ''.join(API_PEM_B64.strip().split())
    pad = len(clean) % 4
    if pad:
        clean += "=" * (4 - pad)

    decoded = base64.b64decode(clean)

    if bytes_is_pem(decoded):
        pem_bytes = decoded
        print("Decoded input is PEM text.")
    else:
        print("Decoded input looks like DER/binary; converting to PEM wrapper.")
        b64_der = base64.encodebytes(decoded)
        pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"

    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
    tf.write(pem_bytes)
    tf.flush(); tf.close()
    pem_temp_path = tf.name
    print("✅ Wrote PEM to", pem_temp_path)

except Exception as e:
    raise SystemExit(f"❌ Failed to decode/write PEM: {type(e).__name__} {e}")

# --- create Coinbase REST client
try:
    client = RESTClient(key_file=pem_temp_path, api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created using key_file + API_KEY/API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {type(e).__name__} {e}")

# --- Example usage: get accounts
try:
    accounts = client.get_accounts()
    print("💰 Accounts fetched successfully:", accounts)
except Exception as e:
    print("❌ Error fetching accounts:", type(e).__name__, e)
