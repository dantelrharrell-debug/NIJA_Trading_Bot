import os
import time
import coinbase_advanced_py as cb

print("🚀 Starting NIJA Bot LIVE TRADING...")

# 1️⃣ Get API keys
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ Missing Coinbase API key or secret. Stop!")
    exit()

# 2️⃣ Connect to Coinbase (LIVE)
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Connected to Coinbase successfully!")
except Exception as e:
    print(f"❌ Could not connect to Coinbase: {e}")
    exit()

# 3️⃣ Bot settings
TRADE_COIN = "BTC-USD"       # Coin to trade
MIN_TRADE_USD = 1            # Minimum USD per trade
MAX_TRADE_USD = 10           # Max USD per trade
SLEEP_SEC = 30               # Time between checking signals

# 4️⃣ Main live trading loop
while True:
    try:
        # ✅ Get account balance
        accounts = client.get_accounts()
        usd_balance = next((float(a.balance) for a in accounts if a.currency == "USD"), 0)
        print(f"💰 USD Balance: ${usd_balance:.2f}")

        if usd_balance < MIN_TRADE_USD:
            print("⚠ Not enough USD to trade. Waiting...")
            time.sleep(SLEEP_SEC)
            continue

        # 🔹 Example signal logic: simple placeholder
        # Replace this with your TradingView signal logic
        signal = "buy"  # or "sell" based on your strategy

        # 🔹 Decide trade size (aggressive but safe)
        trade_amount = min(MAX_TRADE_USD, usd_balance)
        print(f"⚡ Signal: {signal.upper()} | Trade size: ${trade_amount:.2f}")

        # 5️⃣ Place LIVE trade
        order = client.place_order(
            product_id=TRADE_COIN,
            side=signal,
            order_type="market",
            funds=str(trade_amount)  # USD amount
        )
        print(f"✅ Trade executed: {order}")

    except Exception as e:
        print(f"❌ Error during trading: {e}")

    time.sleep(SLEEP_SEC)
