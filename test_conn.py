# test_conn.py
import os
import ccxt
from dotenv import load_dotenv
load_dotenv()

print("ENV DRY_RUN:", os.getenv("DRY_RUN"))

# Try spot client
try:
    spot = ccxt.coinbasepro({
        "apiKey": os.getenv("COINBASE_SPOT_KEY"),
        "secret": os.getenv("COINBASE_SPOT_SECRET"),
        "enableRateLimit": True,
    })
    bal = spot.fetch_balance()
    print("Spot balance keys:", list(bal.keys()))
    print("Spot free balances sample:", {k: bal['free'][k] for k in list(bal['free'])[:5]})
except Exception as e:
    print("Spot client error:", repr(e))

# Try placing a VERY small test order in DRY_RUN (do not execute live here)
try:
    t = spot.fetch_ticker('BTC-USD')
    print("Ticker BTC-USD last:", t.get('last') or t.get('close'))
except Exception as e:
    print("Ticker fetch error:", repr(e))
