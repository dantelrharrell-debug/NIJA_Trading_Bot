# ------------------------------
# NIJA Bot Coinbase RESTClient Setup
# ------------------------------

import os
import tempfile
import traceback
from dotenv import load_dotenv
from coinbase.rest import RESTClient

# Load environment variables from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
SANDBOX = True  # keep sandbox mode for testing

# ------------------------------
# Robust REST client instantiation with logging
# ------------------------------

client = None
pem_temp_path = None
instantiated_with = None

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

# If API_PEM exists, write it to a temp file
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

# Try creating RESTClient using PEM file
def try_create_restclient_with_keyfile(path):
    try:
        print("ℹ️ Trying RESTClient(key_file=... )")
        c = RESTClient(key_file=path, base_url="api.coinbase.com")
        print("✅ RESTClient instantiated with key_file.")
        return c
    except Exception as e:
        print_exc("RESTClient(key_file) failed", e)
        return None

# Try creating RESTClient using api_key + api_secret
def try_create_restclient_with_keypair(key, secret):
    try:
        print("ℹ️ Trying RESTClient(api_key=..., api_secret=...)")
        c = RESTClient(api_key=key, api_secret=secret, base_url="api.coinbase.com")
        print("✅ RESTClient instantiated with api_key+api_secret.")
        return c
    except Exception as e:
        print_exc("RESTClient(api_key+api_secret) failed", e)
        return None

# 1️⃣ Try PEM first
if pem_temp_path:
    client = try_create_restclient_with_keyfile(pem_temp_path)
    instantiated_with = "key_file" if client else None

# 2️⃣ If PEM failed, try api_key + api_secret
if not client and API_KEY and API_SECRET:
    client = try_create_restclient_with_keypair(API_KEY, API_SECRET)
    instantiated_with = "api_key+api_secret" if client else instantiated_with

# 3️⃣ Fail safe
if not client:
    print("⚠️ Could not instantiate REST client with PEM or api_key/secret.")
    if not DRY_RUN:
        print("❌ Exiting because DRY_RUN is False and client creation failed.")
        raise SystemExit(1)
    else:
        print("ℹ️ Continuing in DRY_RUN mode without a live client.")

print("ℹ️ Client type:", type(client), "instantiated_with:", instantiated_with)

# ------------------------------
# Test call (optional, shows account balances if client is live)
# ------------------------------
if client:
    try:
        accounts = client.get_accounts()
        print("💰 Accounts fetched successfully:", accounts)
    except Exception as e:
        print_exc("Failed to fetch accounts", e)
