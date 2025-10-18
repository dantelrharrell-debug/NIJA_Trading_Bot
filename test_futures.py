import ccxt

# Replace with your API keys
api_key = 8cf12748-3ec7-42ac-ab9a-30326dce5d53
api_secret = nMHcCAQEEIJqsooA4D2qcZ0i18AHDlDWmLc4x/iRsvTCXeyQYa7EIoAoGCCqGSM49\nAwEHoUQDQgAEoSbeGCjlKyKo8ozt7KK1Swan8bT9UB4K0P52vsaOmSImiYh1Tkp5\nE84GOz4FhJVOJzcEbuNCLfLpUvYnfHDzFA
api_passphrase = "YOUR_FUTURES_PASSPHRASE"

exchange = ccxt.coinbasepro({
    "apiKey": 8cf12748-3ec7-42ac-ab9a-30326dce5d53
    "secret": api_secret nMHcCAQEEIJqsooA4D2qcZ0i18AHDlDWmLc4x/iRsvTCXeyQYa7EIoAoGCCqGSM49\nAwEHoUQDQgAEoSbeGCjlKyKo8ozt7KK1Swan8bT9UB4K0P52vsaOmSImiYh1Tkp5\nE84GOz4FhJVOJzcEbuNCLfLpUvYnfHDzFA
    "password": api_passphrase,
    "enableRateLimit": True,
})

try:
    balance = exchange.fetch_balance()
    print("✅ Key works! Balance info:")
    print(balance)
except Exception as e:
    print("❌ Key did not work:", e)
