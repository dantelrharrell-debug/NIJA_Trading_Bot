import os
import time
import logging
from dotenv import load_dotenv
import coinbase_advanced_py as cb

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
MIN_RISK = float(os.getenv("MIN_RISK", 0.02))   # 2%
MAX_RISK = float(os.getenv("MAX_RISK", 0.10))   # 10%
MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", 10))

# Setup logging
logging.basicConfig(
    filename='trades.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Coinbase Advanced client
client = cb.Client(api_key=API_KEY, api_secret=API_SECRET)

def calculate_trade_amount(account_balance):
    """Calculate trade amount based on adaptive AI risk logic"""
    risk_percent = MIN_RISK + (MAX_RISK - MIN_RISK) * 0.5  # Example AI adjustment (0.5 = mid)
    trade_amount = account_balance * risk_percent
    return max(trade_amount, MIN_TRADE_AMOUNT)

def place_order(symbol, side, trade_amount):
    """Place order and log it"""
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type='market',
            funds=trade_amount
        )
        logging.info(f"Trade executed: {side} {symbol} ${trade_amount}")
        print(f"Trade executed: {side} {symbol} ${trade_amount}")
        return order
    except Exception as e:
        logging.error(f"Order failed: {e}")
        print(f"Order failed: {e}")

def main():
    while True:
        try:
            account = client.get_account('USD')  # Get account balance
            balance = float(account['available'])
            
            if balance >= MIN_TRADE_AMOUNT:
                trade_amount = calculate_trade_amount(balance)
                # Example trading logic: AI decides buy or sell
                symbol = 'BTC-USD'
                side = 'buy'  # Your AI logic should set this dynamically
                place_order(symbol, side, trade_amount)
            else:
                print("Balance too low for minimum trade amount")
            
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            print(f"Main loop error: {e}")
        
        time.sleep(60)  # Loop every 60 seconds

if __name__ == "__main__":
    main()
