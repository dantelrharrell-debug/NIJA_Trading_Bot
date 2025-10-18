# test_conn.py
import os
from dotenv import load_dotenv
load_dotenv()

import ccxt

print("ENV DRY_RUN:", os.getenv("DRY_RUN"))

try:
    spot = ccxt.coinbase({                       # use 'coinbase' for Coinbase Advanced (not coinbasepro)
        "apiKey": os.getenv("COINBASE_SPOT_KEY"),
        "secret": os.getenv("COINBASE_SPOT_SECRET"),
        "enableRateLimit": True,
    })
    bal = spot.fetch_balance()
    print("Spot balance keys:", list(bal.keys()))
    # print a small sample (safe): list the first 6 free balances if available
    free = bal.get("free", {})
    sample_keys = list(free.keys())[:6]
    print("Spot free balances sample:", {k: free[k] for k in sample_keys})
except Exception as e:
    print("Spot client error:", repr(e))

try:
    # try a ticker fetch for BTC-USD
    t = spot.fetch_ticker('BTC-USD')
    print("Ticker BTC-USD last:", t.get('last') or t.get('close'))
except Exception as e:
    print("Ticker fetch error:", repr(e))
