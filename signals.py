# signals.py
# Pre-configured for 6 active futures coins: BTC, ETH, SOL, XRP, ADA, LTC
# Replace with your real Nija signals as needed

def get_nija_signals():
    # Example signals, can be updated dynamically from your bot logic
    return {
        "BTC": "long",   # profit when price rises
        "ETH": "short",  # profit when price falls
        "SOL": "long",
        "XRP": "short",
        "ADA": "long",
        "LTC": "short"
    }
