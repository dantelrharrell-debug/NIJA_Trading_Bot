import os
from time import sleep
import coinbase_advanced_py as cb

# ✅ Environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"

TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD,LTC-USD").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "10"))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

# Stop-loss and take-profit (percentages)
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2"))  # 2% loss
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "3"))  # 3% gain

# Check keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# Initialize Coinbase client
client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("✅ Coinbase client initialized")

# Track open positions
positions = {symbol: None for symbol in TRADE_SYMBOLS}

# Example: print balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Error fetching balances:", e)

# Trading loop
while True:
    for symbol in TRADE_SYMBOLS:
        try:
            price = float(client.get_product_price(symbol))
            print(f"📈 Current price of {symbol}: {price}")

            # If no position, place market buy order
            if positions[symbol] is None:
                # Uncomment to activate real trade
                # order = client.place_market_order(symbol, "buy", TRADE_AMOUNT)
                entry_price = price
                positions[symbol] = entry_price
                print(f"🟢 Bought {symbol} at {entry_price}")

            # Check stop-loss / take-profit
            else:
                entry_price = positions[symbol]
                loss_threshold = entry_price * (1 - STOP_LOSS_PCT / 100)
                profit_threshold = entry_price * (1 + TAKE_PROFIT_PCT / 100)

                if price <= loss_threshold:
                    # Uncomment to sell
                    # client.place_market_order(symbol, "sell", TRADE_AMOUNT)
                    print(f"🔴 Stop-loss triggered for {symbol} at {price}")
                    positions[symbol] = None

                elif price >= profit_threshold:
                    # Uncomment to sell
                    # client.place_market_order(symbol, "sell", TRADE_AMOUNT)
                    print(f"🏆 Take-profit triggered for {symbol} at {price}")
                    positions[symbol] = None

        except Exception as e:
            print(f"❌ Trading error for {symbol}:", e)

    sleep(SLEEP_INTERVAL)
