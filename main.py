import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Coinbase client import
try:
    from coinbase_advanced_py import Client
    logging.info("✅ Coinbase client module loaded")
except ModuleNotFoundError:
    logging.error("❌ Coinbase client module NOT FOUND")
    raise

# Initialize client
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = None
try:
    client = Client(API_KEY, API_SECRET)
    logging.info("✅ Coinbase client initialized successfully")
except Exception as e:
    logging.error(f"❌ Failed to initialize Coinbase client: {e}")

# Trading configuration
TRADING_PAIRS = ["BTC-USD", "ETH-USD", "LTC-USD"]
ALLOCATION = 100  # USD per trade, can be adjusted
TRADE_INTERVAL = 60  # seconds between checks

# Safe order execution
def place_order(symbol, side, amount):
    if not client:
        logging.warning("Client not initialized. Skipping order.")
        return
    try:
        logging.info(f"Placing {side} order for {symbol} amount {amount}")
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type='market',
            funds=str(amount)
        )
        logging.info(f"✅ Order executed: {order}")
    except Exception as e:
        logging.error(f"❌ Failed to place order: {e}")

# Simple example strategy (can be replaced with real signals)
def trading_strategy(symbol):
    # Dummy strategy: Buy on even minutes, sell on odd
    minute = int(time.time() / 60)
    if minute % 2 == 0:
        return "buy"
    else:
        return "sell"

# Main trading loop
def main():
    logging.info("🚀 Starting autonomous trading bot")
    while True:
        for pair in TRADING_PAIRS:
            side = trading_strategy(pair)
            place_order(pair, side, ALLOCATION)
        time.sleep(TRADE_INTERVAL)

# Run the bot
if __name__ == "__main__":
    main()
