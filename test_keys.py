import ccxt

# Replace these with your actual keys from .env
SPOT_KEY = 'YOUR_SPOT_KEY'
SPOT_SECRET = 'YOUR_SPOT_SECRET'

FUTURES_KEY = 'YOUR_FUTURES_KEY'
FUTURES_SECRET = 'YOUR_FUTURES_SECRET'

def test_coinbase_spot():
    try:
        client = ccxt.coinbase({
            'apiKey': SPOT_KEY,
            'secret': SPOT_SECRET,
        })
        markets = client.load_markets()
        print("✅ Spot API keys are valid!")
        print(f"Available spot markets: {list(markets.keys())[:10]} ...")
    except ccxt.AuthenticationError:
        print("❌ Spot API keys are INVALID or missing permissions!")
    except Exception as e:
        print(f"⚠️ Spot API error: {e}")

def test_coinbase_futures():
    try:
        client = ccxt.coinbase({
            'apiKey': FUTURES_KEY,
            'secret': FUTURES_SECRET,
        })
        markets = client.load_markets()
        print("✅ Futures API keys are valid!")
        print(f"Available futures markets: {list(markets.keys())[:10]} ...")
    except ccxt.AuthenticationError:
        print("❌ Futures API keys are INVALID or missing permissions!")
    except Exception as e:
        print(f"⚠️ Futures API error: {e}")

if __name__ == "__main__":
    print("Testing Coinbase Spot API keys...")
    test_coinbase_spot()
    print("\nTesting Coinbase Futures API keys...")
    test_coinbase_futures()
