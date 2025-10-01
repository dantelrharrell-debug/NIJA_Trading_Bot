import coinbase_advanced_py as cb

# === YOUR API KEYS ===
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"

# === Connect to Coinbase Advanced ===
client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret)

# === Risk Settings ===
STARTING_BALANCE = 17.95  # Your account balance
MIN_RISK = 0.02           # 2%
MAX_RISK = 0.10           # 10%

# === Function to calculate trade size based on risk % ===
def calc_trade_size(balance, risk_percent):
    return round(balance * risk_percent, 2)  # rounded to 2 decimal places for USD

# === Example: trade BTC-USD with 5% risk ===
risk_percent = 0.05  # Change between 0.02–0.10 for 2–10%
trade_amount = calc_trade_size(STARTING_BALANCE, risk_percent)

# === Place a market buy order ===
try:
    order = client.create_order(
        symbol="BTC-USD",
        side="buy",
        type="market",
        quantity=trade_amount / client.get_ticker("BTC-USD")['price']  # convert USD to BTC
    )
    print("Trade executed:", order)
except Exception as e:
    print("Error placing trade:", e)

# === Check account balances ===
balance = client.get_accounts()
print("Updated account balances:", balance)
