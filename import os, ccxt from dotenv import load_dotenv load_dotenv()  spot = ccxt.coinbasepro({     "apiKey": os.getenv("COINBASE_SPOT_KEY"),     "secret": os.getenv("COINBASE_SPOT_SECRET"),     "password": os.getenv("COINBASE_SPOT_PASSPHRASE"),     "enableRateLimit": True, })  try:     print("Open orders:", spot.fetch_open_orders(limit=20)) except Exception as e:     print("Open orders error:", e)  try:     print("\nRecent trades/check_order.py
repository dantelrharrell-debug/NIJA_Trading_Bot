import os, ccxt
from dotenv import load_dotenv
load_dotenv()

spot = ccxt.coinbasepro({
    "apiKey": os.getenv("COINBASE_SPOT_KEY"),
    "secret": os.getenv("COINBASE_SPOT_SECRET"),
    "password": os.getenv("COINBASE_SPOT_PASSPHRASE"),
    "enableRateLimit": True,
})

try:
    print("Open orders:", spot.fetch_open_orders(limit=20))
except Exception as e:
    print("Open orders error:", e)

try:
    print("\nRecent trades/fills:")
    trades = spot.fetch_my_trades(symbol='BTC-USD', limit=50)
    for t in trades:
        print(t)
except Exception as e:
    print("Fetch trades error:", e)
