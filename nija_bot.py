import os
from time import sleep
import coinbase_advanced_py as cb

# =====================
# Environment Variables
# =====================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = False  # Live trading
TRADE_SYMBOLS = ["BTC-USD", "ETH-USD", "LTC-USD"]  # Add all your symbols
MIN_RISK_PERCENT = 2  # 2% of account per trade
MAX_RISK_PERCENT = 10  # 10% of account per trade
SLEEP_INTERVAL = 10  # seconds

# Stop-loss and take-profit settings (percentages)
STOP_LOSS_PERCENT = 2  # 2% loss
TAKE_PROFIT_PERCENT = 5  # 5% profit

# =====================
# Initialization
# =====================
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("🚀 Coinbase live client initialized")

# Confirm connection by fetching balances
try:
    balances = client.get_account_balances()
    total_usd = balances.get("USD", 0)
    print(f"💰 USD Balance: {total_usd}")
except Exception as e:
    print("❌ Error fetching balances:", e)
    exit(1)

# =====================
# Helper Functions
# =====================
def calculate_target_prices(entry_price):
    """Return stop-loss and take-profit prices based on entry price."""
    stop_loss = entry_price * (1 - STOP_LOSS_PERCENT / 100)
    take_profit = entry_price * (1 + TAKE_PROFIT_PERCENT / 100)
    return stop_loss, take_profit

def calculate_trade_amount(balance):
    """Calculate dynamic trade amount between min and max % of account."""
    min_trade = balance * (MIN_RISK_PERCENT / 100)
    max_trade = balance * (MAX_RISK_PERCENT / 100)
    # For simplicity, pick average
    return (min_trade + max_trade) / 2

# =====================
# Trading Loop
# =====================
open_positions = {}  # {symbol: entry_price}

while True:
    try:
        balances = client.get_account_balances()
        total_usd = balances.get("USD", 0)
    except Exception as e:
        print("❌ Error fetching balances:", e)
        sleep(SLEEP_INTERVAL)
        continue

    for symbol in TRADE_SYMBOLS:
        try:
            current_price = client.get_product_price(symbol)
            print(f"📈 {symbol} current price: {current_price}")

            trade_amount = calculate_trade_amount(total_usd)

            # Open position if not already open
            if symbol not in open_positions:
                client.place_market_order(symbol, "buy", trade_amount)
                open_positions[symbol] = current_price
                stop_loss, take_profit = calculate_target_prices(current_price)
                print(f"✅ Opened LIVE position for {symbol} at {current_price} | Trade amount: {trade_amount}")
                print(f"   Stop-loss: {stop_loss}, Take-profit: {take_profit}")
                continue

            # Manage existing positions
            entry_price = open_positions[symbol]
            stop_loss, take_profit = calculate_target_prices(entry_price)

            # Check stop-loss
            if current_price <= stop_loss:
                client.place_market_order(symbol, "sell", trade_amount)
                print(f"⚠️ {symbol} hit STOP-LOSS at {current_price} — position closed")
                open_positions.pop(symbol)
                continue

            # Check take-profit
            if current_price >= take_profit:
                client.place_market_order(symbol, "sell", trade_amount)
                print(f"🏆 {symbol} hit TAKE-PROFIT at {current_price} — position closed")
                open_positions.pop(symbol)
                continue

        except Exception as e:
            print(f"❌ Trading error for {symbol}: {e}")

    sleep(SLEEP_INTERVAL)
