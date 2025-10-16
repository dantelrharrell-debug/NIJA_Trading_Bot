#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

if USE_MOCK:
    print("✅ Mock mode is ON — skipping live Coinbase test.")
else:
    try:
        import coinbase_advanced_py as cb

        # Load API keys from environment variables
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PEM_B64 = os.getenv("API_PEM_B64")

        # Initialize client
        client = cb.CoinbaseAdvanced(
            key=API_KEY,
            secret=API_SECRET,
            pem_b64=API_PEM_B64,
            sandbox=False  # False for live trading
        )

        # Test account info
        accounts = client.get_accounts()
        print("✅ Coinbase LIVE connection OK. Accounts found:")
        for acc in accounts:
            print(f"- {acc['currency']}: {acc['available']} available")

    except Exception as e:
        print("❌ Coinbase LIVE connection FAILED:", e)
        raise
