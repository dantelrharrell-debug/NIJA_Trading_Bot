#!/usr/bin/env python3
import os
import tempfile
import traceback
from coinbase.rest import RESTClient

# --- Load env ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")  # if you have a private key PEM string
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "api.coinbase.com")  # optional override

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

client = None
pem_temp_path = None
instantiated_with = None

# If user provided a PEM string, write it to a temp file (preserves newlines)
if API_PEM:
    try:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM.encode("utf-8"))
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote API_PEM to temporary file:", pem_temp_path)
    except Exception as e:
        print_exc("Failed to write API_PEM to temp file", e)
        pem_temp_path = None

# Try create REST client using key file only (do NOT pass api_key with key_file)
def try_create_restclient_with_keyfile(path):
    try:
        print("ℹ️ Trying RESTClient(key_file=...)")
        c = RESTClient(key_file=path, base_url=BASE_URL)
        print("✅ RESTClient instantiated with key_file.")
        return c
    except Exception as e:
        print_exc("RESTClient(key_file) failed", e)
        return None

# Try create REST client using api_key + api_secret
def try_create_restclient_with_keypair(key, secret):
    try:
        print("ℹ️ Trying RESTClient(api_key=..., api_secret=...)")
        c = RESTClient(api_key=key, api_secret=secret, base_url=BASE_URL)
        print("✅ RESTClient instantiated with api_key+api_secret.")
        return c
    except Exception as e:
        print_exc("RESTClient(api_key+api_secret) failed", e)
        return None

# Order: try PEM key_file first (if provided), else api key/secret
if pem_temp_path:
    client = try_create_restclient_with_keyfile(pem_temp_path)
    instantiated_with = "key_file" if client else None

if not client and API_KEY and API_SECRET:
    client = try_create_restclient_with_keypair(API_KEY, API_SECRET)
    instantiated_with = instantiated_with or ("api_key+api_secret" if client else None)

if not client:
    print("⚠️ Could not instantiate REST client with PEM or api_key/secret.")
    if not DRY_RUN:
        print("❌ Exiting because DRY_RUN is False and client creation failed.")
        raise SystemExit(1)
    else:
        print("ℹ️ Continuing in DRY_RUN mode without a live client.")

print("ℹ️ Client type:", type(client), "instantiated_with:", instantiated_with)

# Example read-only call (accounts)
if client and not DRY_RUN:
    try:
        accounts = client.get_accounts()
        print("✅ Accounts fetched:")
        for a in accounts:
            bal = a.get("balance", {})
            print(f" - {a.get('name')} : {bal.get('amount')} {bal.get('currency')}")
    except Exception as e:
        print_exc("Failed to fetch accounts", e)
else:
    print("ℹ️ Skipping account fetch because no client or DRY_RUN=True")

# Put your trading logic below; respect DRY_RUN to avoid live trades during testing
def example_trade():
    if DRY_RUN:
        print("ℹ️ DRY_RUN is True — not executing live trades.")
        return
    if not client:
        print("⚠️ No client available — cannot trade.")
        return
    try:
        print("ℹ️ (placeholder) execute trade logic here")
        # e.g. client.place_order(...) depending on library API
    except Exception as e:
        print_exc("Trade failed", e)

# Example run
example_trade()
