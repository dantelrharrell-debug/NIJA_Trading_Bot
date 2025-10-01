import os
import coinbase_advanced_py as cb

# Replace with your actual API keys
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret)

# Test connection and print balances
balance = client.get_accounts()
print("Your account balances:", balance)

# Now you can add trading logic here
# Example: client.place_order(...) once you know your strategy
