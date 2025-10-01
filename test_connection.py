import coinbase_advanced_py as cb

api_key = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
api_secret = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret)

balance = client.get_accounts()
print(balance)
