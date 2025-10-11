# --- Simple Coinbase REST Client with API Key only ---
import os
import traceback
from coinbase.rest import RESTClient

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

client = None

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

if API_KEY and API_SECRET:
    try:
        print("ℹ️ Creating RESTClient with API_KEY + API_SECRET...")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient ready!")
    except Exception as e:
        print_exc("RESTClient creation failed", e)

if not client:
    print("⚠️ Could not create REST client.")
    if not DRY_RUN:
        print("❌ Exiting because DRY_RUN is False.")
        raise SystemExit(1)
    else:
        print("ℹ️ Continuing in DRY_RUN mode without live client.")

# --- Example: fetch accounts ---
if client and not DRY_RUN:
    try:
        accounts = client.get_accounts()
        print("✅ Accounts fetched:")
        for a in accounts:
            print(f" - {a['name']}: {a['balance']['amount']} {a['balance']['currency']}")
    except Exception as e:
        print_exc("Failed to fetch accounts", e)
# --- Simple Coinbase REST Client setup ---
import os
import traceback
from coinbase.rest import RESTClient

# Load environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
SANDBOX = os.getenv("SANDBOX", "True").lower() == "true"

client = None

def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

# Try to instantiate RESTClient with API_KEY + API_SECRET
if API_KEY and API_SECRET:
    try:
        print("ℹ️ Trying RESTClient(api_key + api_secret)...")
        client = RESTClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            base_url="https://api.coinbase.com"
        )
        print("✅ RESTClient instantiated with API_KEY + API_SECRET.")
    except Exception as e:
        print_exc("Failed to instantiate RESTClient", e)
        client = None

# Handle failure
if not client:
    print("⚠️ Could not create REST client.")
    if not DRY_RUN:
        print("❌ Exiting because DRY_RUN is False and client creation failed.")
        raise SystemExit(1)
    else:
        print("ℹ️ Continuing in DRY_RUN mode without a live client.")

print("ℹ️ Client ready:", type(client))

# --- Example: check accounts (sandbox mode) ---
if client and not DRY_RUN:
    try:
        accounts = client.get_accounts()
        print("✅ Accounts fetched:")
        for a in accounts:
            print(f" - {a['name']}: {a['balance']['amount']} {a['balance']['currency']}")
    except Exception as e:
        print_exc("Failed to fetch accounts", e)
