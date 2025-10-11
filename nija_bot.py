# nija_bot.py
import os
import base64
import tempfile
import traceback
from coinbase.rest import RESTClient

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

pem_temp_path = None
API_PEM_B64 = os.getenv("API_PEM_B64")

if API_PEM_B64:
    try:
        # remove whitespace and auto-pad
        clean = "".join(API_PEM_B64.strip().split())
        pad = len(clean) % 4
        if pad != 0:
            clean += "=" * (4 - pad)
        pem_bytes = base64.b64decode(clean)
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(pem_bytes)
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote PEM to", pem_temp_path)
    except Exception as e:
        print_exc("Failed to decode/write PEM", e)

# Create client
client = None
try:
    if pem_temp_path:
        client = RESTClient(key_file=pem_temp_path)
    else:
        # fallback: allow API_KEY/API_SECRET env usage if you prefer
        api_key = os.getenv("API_KEY")
        api_secret = os.getenv("API_SECRET")
        if api_key and api_secret:
            # rest client may accept those args depending on library usage
            client = RESTClient(api_key=api_key, api_secret=api_secret)
        else:
            raise SystemExit("❌ No PEM file and no API_KEY/API_SECRET - cannot create client")

    # quick smoke test
    accounts = client.get_accounts()
    print("✅ Coinbase REST client started; accounts fetched:", accounts)
except Exception as e:
    print_exc("Failed to start Coinbase client", e)
    raise
