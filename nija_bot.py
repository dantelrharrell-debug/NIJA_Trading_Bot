import os
import json
import coinbase_advanced_py as cb
from time import sleep

# =========================
# Config from environment
# =========================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"

TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD").split(",")
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "1.0")) / 100
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", "1.0")) / 100

TRADES_FILE = "active_trades.json"

# =========================
# Validate API Keys
# =========================
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# =========================
# Initialize Coinbase client
# =========================
try:
    client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
    print("🚀 Coinbase client initialized")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# =========================
# Load persistent trades
# =========================
if os.path.exists(TRADES_FILE):
    with open(TRADES_FILE, "r") as f:
        active_trades = json.load(f)
    print("🔄 Loaded active trades:", active_trades)
else:
    active_trades = {}

# =========================
# Save trades helper
# =========================
def save_trades():
    with open(TRADES_FILE, "w") as f:
        json.dump(active_trades, f)
    print("💾 Trades saved")

# =========================
# Helper: calculate dynamic amount per trade (aggressive but safe)
# =========================
def get_trade_amount(symbol, risk_percent=2.0):
    try:
        balances = client.get_account_balances()
        usd_balance = balances.get("USD", 0)
        amount = usd_balance * (risk_percent / 100)
        print(f"💵 Calculated trade amount for {symbol}: {amount} USD")
        return amount
    except Exception as e:
        print("❌ Failed to fetch balances:", e)
        return 0

# =========================
# Main trading loop
# =========================
while True:
    for symbol in TRADE_SYMBOLS:
        try:
            current_price = client.get_product_price(symbol)
            print(f"📈 Current price of {symbol}: {current_price}")

            # Determine dynamic trade amount
            trade_amount = get_trade_amount(symbol, risk_percent=5)  # 5% of USD balance

            # Place a market buy if not already active
            if symbol not in active_trades and trade_amount > 0:
                # Uncomment for live trading
                # client.place_market_order(symbol, "buy", trade_amount)
                active_trades[symbol] = {"buy_price": current_price, "amount": trade_amount}
                save_trades()
                print(f"✅ Bought {trade_amount} USD of {symbol} at {current_price}")

            # Check stop-loss
            if symbol in active_trades:
                buy_price = active_trades[symbol]["buy_price"]
                if current_price <= buy_price * (1 - STOP_LOSS_PERCENT):
                    # Uncomment for live trading
                    # client.place_market_order(symbol, "sell", active_trades[symbol]["amount"])
                    print(f"⚠️ Stop-loss triggered for {symbol} at {current_price}")
                    del active_trades[symbol]
                    save_trades()

                # Check take-profit
                elif current_price >= buy_price * (1 + TAKE_PROFIT_PERCENT):
                    # Uncomment for live trading
                    # client.place_market_order(symbol, "sell", active_trades[symbol]["amount"])
                    print(f"🏆 Take-profit triggered for {symbol} at {current_price}")
                    del active_trades[symbol]
                    save_trades()

        except Exception as e:
            print(f"❌ Trading error for {symbol}: {e}")

    sleep(SLEEP_INTERVAL)
