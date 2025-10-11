import os, base64, tempfile
from coinbase.rest import RESTClient

API_PEM_B64 = os.getenv("API_PEM_B64")
pem_temp_path = None

def bytes_is_pem(b: bytes) -> bool:
    return b.startswith(b"-----BEGIN")

if API_PEM_B64:
    try:
        # Clean whitespace/newlines that might have been added in the UI
        clean = ''.join(API_PEM_B64.strip().split())
        # Pad if needed
        pad = len(clean) % 4
        if pad:
            clean += '=' * (4 - pad)

        decoded = base64.b64decode(clean)

        # If decoded bytes are already ASCII PEM, write as text; otherwise convert DER->PEM
        if bytes_is_pem(decoded):
            mode = "wb"
            pem_bytes = decoded  # already PEM ASCII in bytes
            print("Decoded input is PEM text.")
        else:
            # Assume decoded is DER private key bytes (binary). Convert to PEM.
            print("Decoded input looks like DER/binary; converting to PEM wrapper.")
            b64_der = base64.encodebytes(decoded)  # includes newlines
            # Create proper PEM bytes (ensure correct header)
            pem_bytes = b"-----BEGIN PRIVATE KEY-----\n" + b64_der + b"-----END PRIVATE KEY-----\n"
            mode = "wb"

        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(pem_bytes)
        tf.flush(); tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote PEM to", pem_temp_path)
    except Exception as e:
        print("❌ Failed to decode/write PEM:", type(e).__name__, e)

# --- create client
if pem_temp_path:
    try:
        client = RESTClient(key_file=pem_temp_path)
        print("✅ RESTClient created using key_file")
    except Exception as e:
        print("❌ Failed to start Coinbase client:", type(e).__name__, e)
else:
    print("❌ PEM file not available, cannot start client")
