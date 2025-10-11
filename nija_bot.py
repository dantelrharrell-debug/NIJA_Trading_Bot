# nija_bot.py
import os
import traceback
from coinbase.rest import RESTClient

# --- Load environment variables ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

client = None

# --- Helper for printing exceptions ---
def print_exc(label, e):
    print(f"❌ {label}: {type(e).__name__}: {e}")
    traceback.print_exc()

# --- Create REST client using API_KEY + API_SECRET ---
if API_KEY and API_SECRET:
    try:
        print("ℹ️ Creating RESTClient with API_KEY + API_SECRET...")
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ RESTClient ready!")
    except Exception as e:
        print_exc("RESTClient creation failed", e)

# --- Handle case where client cannot be created ---
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

# --- Your trading logic starts here ---
# Example: placeholder function for a trade
def example_trade():
    if DRY_RUN:
        print("ℹ️ DRY_RUN: Skipping live trade")
        return
    try:
        print("ℹ️ Example trade executed (replace with real logic)")
        # Add your buy/sell calls here using client
    except Exception as e:
        print_exc("Trade failed", e)

# Run example trade
example_trade()
