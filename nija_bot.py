import sys
print("sys.executable:", sys.executable)
print("python version:", sys.version)
import os
import base64
import tempfile
import traceback

# --- Try API key + secret first (recommended) ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
pem_temp_path = None

# If you have a base64-encoded key file in env, decode to bytes and write as temp file
API_PEM_B64 = os.getenv("API_PEM_B64")
if API_PEM_B64:
    try:
        # sanitize & pad
        b64 = ''.join(API_PEM_B64.strip().split())
        pad = len(b64) % 4
        if pad:
            b64 += '=' * (4 - pad)
        pem_bytes = base64.b64decode(b64)
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(pem_bytes)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote key bytes to", pem_temp_path)
        # show first bytes for debugging (hex)
        with open(pem_temp_path, "rb") as f:
            first = f.read(64)
        print("First 64 bytes (hex):", first.hex())
    except Exception as e:
        print("❌ Failed to decode/write PEM:", e)
        traceback.print_exc()

# --- Create Coinbase client (prefer API keys) ---
client = None
try:
    if API_KEY and API_SECRET:
        # preferred: use key + secret so library won't try to read files as JSON
        from coinbase.rest import RESTClient
        print("ℹ️ Creating RESTClient using API_KEY + API_SECRET...")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient created with API_KEY/API_SECRET")
    elif pem_temp_path:
        # fallback: user provided file — but the lib appears to expect JSON.
        # We'll attempt to create client but catch Unicode/JSON errors and print file preview.
        from coinbase.rest import RESTClient
        try:
            print("ℹ️ Creating RESTClient using key_file (fallback)...")
            client = RESTClient(key_file=pem_temp_path)
            print("✅ RESTClient created with key_file")
        except Exception as e:
            print("❌ RESTClient failed when using key_file:", type(e).__name__, e)
            # give useful debug output showing file type and a small text preview safely
            try:
                with open(pem_temp_path, "rb") as f:
                    data = f.read(512)
                # determine if file looks like text PEM or JSON
                text_like = True
                try:
                    data.decode("utf-8")
                except Exception:
                    text_like = False
                print(" - file looks like text PEM?:", text_like)
                print(" - file 1st 200 bytes (repr):", repr(data[:200]))
                # If it appears JSON-ish, show a tiny preview
                if text_like:
                    text = data.decode("utf-8", errors="replace")
                    preview = "\n".join(text.splitlines()[:10])
                    print(" - text preview (first 10 lines):\n" + preview)
            except Exception as de:
                print(" - could not read file for debug:", de)
            raise
    else:
        print("❌ No API_KEY/API_SECRET and no API_PEM_B64 provided. Cannot create REST client.")
except Exception as e:
    print("❌ Failed to start Coinbase client:", type(e).__name__, e)
    traceback.print_exc()

# quick smoke test (only if client exists)
if client:
    try:
        accounts = client.get_accounts()
        print("✅ Accounts fetched (count):", len(accounts) if hasattr(accounts, "__len__") else "unknown")
    except Exception as e:
        print("❌ Error calling get_accounts():", type(e).__name__, e)
        traceback.print_exc()
