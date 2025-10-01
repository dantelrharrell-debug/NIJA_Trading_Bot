# test_connection.py
import coinbase_advanced as cb

# === Your actual API keys ===
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

try:
    # Initialize Coinbase client
    client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)
    
    # Test: Fetch accounts
    accounts = client.get_accounts()
    
    print("✅ Connection successful! Current balances:")
    for acc in accounts:
        print(f"{acc['currency']}: {acc['balance']}")

    # Optional: Test ticker fetch
    test_symbol = "BTC-USD"
    ticker = client.get_ticker(test_symbol)
    print(f"\n✅ Ticker for {test_symbol}:")
    print(ticker)

except Exception as e:
    print("❌ Connection failed:", str(e))
