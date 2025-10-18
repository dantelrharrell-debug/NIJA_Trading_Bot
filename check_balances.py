import coinbase_advanced_py as cb

# Replace with your actual API key and secret
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

# Set your bot's minimum allocation per trade
MIN_ALLOCATION = 10  # USD, adjust to your bot's settings

try:
    # Initialize client
    client = cb.Client(API_KEY, API_SECRET)
    
    # Check USD balance
    usd_balance = client.get_account_balance("USD")
    print(f"USD Balance: {usd_balance}")
    
    if float(usd_balance) < MIN_ALLOCATION:
        print(f"USD balance is below minimum allocation (${MIN_ALLOCATION}) – no trades will execute.")
    
    # Coins to check
    coins = ["BTC", "ETH", "LTC", "SOL", "DOGE", "XRP"]
    
    for coin in coins:
        balance = client.get_account_balance(coin)
        try:
            balance_float = float(balance)
        except:
            balance_float = 0
        if balance_float < MIN_ALLOCATION:
            print(f"{coin} balance (${balance_float}) is below minimum allocation (${MIN_ALLOCATION}) – will be skipped.")
        else:
            print(f"{coin} balance (${balance_float}) meets minimum allocation – can trade.")

except Exception as e:
    print("Error connecting to Coinbase Advanced API:", e)
