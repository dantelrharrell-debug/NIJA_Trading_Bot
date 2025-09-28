import ccxt
from decimal import Decimal
import random
import json

# Configure your Coinbase exchange (spot)
exchange = ccxt.coinbase({
    "apiKey": "YOUR_SPOT_KEY",
    "secret": "YOUR_SPOT_SECRET",
    "enableRateLimit": True
})

# List of tickers to scan daily
TICKERS = ["BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD"]

def ai_score(ticker):
    """AI placeholder: score 0-1, higher is better"""
    # Replace with real AI logic (trend, volatility, volume)
    return random.uniform(0.1, 1.0)

def scan_market():
    """Return tickers sorted by AI score descending"""
    results = []
    for symbol in TICKERS:
        try:
            ticker_data = exchange.fetch_ticker(symbol)
            price = Decimal(str(ticker_data['last']))
            score = ai_score(symbol)
            results.append({
                "symbol": symbol,
                "last_price": price,
                "ai_score": round(score, 2)
            })
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
    results.sort(key=lambda x: x['ai_score'], reverse=True)
    # Save top tickers for webhook use
    with open("ai_top_tickers.json", "w") as f:
        json.dump(results[:5], f)
    return results
