import os
import traceback
from dotenv import load_dotenv
load_dotenv()

# --- Coinbase Client Setup ---
client = None
try:
    from coinbase.wallet.client import Client
    client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    print("Client initialized: coinbase.wallet.Client")
except Exception as e:
    print("Coinbase.wallet.Client import failed, trying advanced client...")
    try:
        import coinbase_advanced_py as cbadv
        client = cbadv.Client(api_key=os.getenv("API_KEY"), api_secret=os.getenv("API_SECRET"))
        print("Client initialized: coinbase_advanced_py.Client")
    except Exception as e:
        print("Failed to initialize any Coinbase client:", e)
        traceback.print_exc()

# --- Account Fetching ---
def fetch_usd_balance():
    if not client:
        print("Client not initialized, returning USD balance = 0")
        return 0
    try:
        # Coinbase Wallet vs Advanced API differences
        if hasattr(client, 'get_accounts'):  # coinbase.wallet.Client
            accounts = client.get_accounts()
            for acc in accounts['data']:
                if acc['currency'] == 'USD':
                    return float(acc['balance']['amount'])
        else:  # coinbase_advanced_py
            accounts = client.get_accounts()  # adjust if needed
            for acc in accounts:
                if acc['currency'] == 'USD':
                    return float(acc['balance'])
    except Exception as e:
        print("Error fetching USD balance:", e)
        traceback.print_exc()
    return 0

usd_balance = fetch_usd_balance()
print("USD balance:", usd_balance)

# --- Trading Logic Example ---
trading_pairs = ["BTCUSD", "ETHUSD", "LTCUSD", "SOLUSD"]
minimum_allocation = 10  # minimum trade allocation in USD

for pair in trading_pairs:
    try:
        allocation = usd_balance * 0.1  # Example: 10% per trade
        if allocation < minimum_allocation:
            print(f"Skipped {pair}: allocation below minimum.")
            continue

        # --- Place trade logic here ---
        print(f"Placing trade for {pair} with allocation ${allocation:.2f}")
        # Example: client.place_order(pair, allocation, order_type="market")

    except Exception as e:
        print(f"Error processing {pair} trade:", e)
        traceback.print_exc()

print("Trading cycle complete.")
