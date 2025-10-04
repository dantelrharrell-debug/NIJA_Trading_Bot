# main.py
import os
import sys
import subprocess
import time

# -------------------------------
# Ensure coinbase_advanced_py is installed
# -------------------------------
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not found. Installing now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.8.2"])
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py installed successfully.")
    except Exception as e:
        print(f"❌ Failed to install coinbase_advanced_py: {e}")
        sys.exit(1)

# -------------------------------
# Load API keys
# -------------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ Coinbase API_KEY or API_SECRET missing. Set them in Render secrets.")
    sys.exit(1)

# -------------------------------
# Initialize Coinbase client
# -------------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Coinbase client: {e}")
    sys.exit(1)

# -------------------------------
# Your trading loop
# -------------------------------
def run_trading_bot():
    print("🚀 Trading bot started. Running...")
    while True:
        try:
            # Example: print account balance
            balances = client.get_account_balances()  # adapt to your API
            print(f"Balances: {balances}")

            # TODO: Add your trading logic here
            # Example:
            # signal = check_signal()
            # if signal == "BUY":
            #     client.place_order("BTC-USD", "buy", 0.01)

        except Exception as e:
            print(f"⚠️ Error during trading loop: {e}")
        
        time.sleep(10)  # pause for 10 seconds before next check

if __name__ == "__main__":
    run_trading_bot()
