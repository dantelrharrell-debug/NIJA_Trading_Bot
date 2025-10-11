#!/usr/bin/env python3
import os, tempfile, traceback
from coinbase.rest import RESTClient

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")    # optional multiline PEM
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "api.coinbase.com")

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

client = None
pem_temp_path = None

if API_PEM:
    try:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM.encode("utf-8"))
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote API_PEM to temp file:", pem_temp_path)
    except Exception as e:
        print_exc("Failed to write API_PEM to temp file", e)
        pem_temp_path = None

def try_keyfile(path):
    try:
        print("ℹ️ Trying RESTClient(key_file=...)")
        return RESTClient(key_file=path, base_url=BASE_URL)
    except Exception as e:
        print_exc("RESTClient(key_file) failed", e)
        return None

def try_keypair(key, secret):
    try:
        print("ℹ️ Trying RESTClient(api_key, api_secret)")
        return RESTClient(api_key=key, api_secret=secret, base_url=BASE_URL)
    except Exception as e:
        print_exc("RESTClient(api_key+api_secret) failed", e)
        return None

if pem_temp_path:
    client = try_keyfile(pem_temp_path)

if not client and API_KEY and API_SECRET:
    client = try_keypair(API_KEY, API_SECRET)

if not client:
    print("⚠️ Could not create client. DRY_RUN =", DRY_RUN)
    if not DRY_RUN:
        raise SystemExit("❌ No client and DRY_RUN is False — exiting.")
else:
    print("✅ RESTClient ready!")

if client and not DRY_RUN:
    try:
        accounts = client.get_accounts()
        print("✅ Accounts fetched:")
        for a in accounts:
            bal = a.get("balance", {})
            print(f" - {a.get('name')}: {bal.get('amount')} {bal.get('currency')}")
    except Exception as e:
        print_exc("Failed to fetch accounts", e)
else:
    print("ℹ️ Skipping account fetch (no client or DRY_RUN=True)")

# Placeholder trade function (do NOT run live unless you understand it)
def example_trade():
    if DRY_RUN:
        print("ℹ️ DRY_RUN=True — not executing trades.")
        return
    if not client:
        print("⚠️ No client — cannot trade.")
        return
    print("ℹ️ (placeholder) trade executed")

example_trade()
