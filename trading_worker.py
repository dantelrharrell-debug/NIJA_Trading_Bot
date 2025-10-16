#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

print(f"⚡ USE_MOCK={USE_MOCK}")

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully.")
except ImportError as e:
    print("❌ Failed to import coinbase_advanced_py:", e)
    exit(1)

# Initialize client
client = None
if not USE_MOCK:
    try:
        client = cb.Coinbase(
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=API_PASSPHRASE
        )
        print("✅ Live Coinbase client initialized.")
    except Exception as e:
        print("❌ Failed to initialize Coinbase client:", e)
        exit(1)
else:
    print("⚡ MOCK mode active, no live client.")

# Example trading loop
def main_loop():
    while True:
        try:
            if USE_MOCK:
                print("⚡ MOCK trade: simulated trade tick")
            else:
                # Example: fetch account balances
                balances = client.get_accounts()
                print("💰 Balances:", balances)
                # Add your trading logic here
            time.sleep(5)  # Poll every 5 seconds
        except KeyboardInterrupt:
            print("🛑 Exiting trading worker.")
            break
        except Exception as e:
            print("❌ Error during trading loop:", e)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
