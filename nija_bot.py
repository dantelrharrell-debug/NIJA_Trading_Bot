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

        # Fetch account info
        accounts = client.get_accounts()
        if not accounts:
            print("⚠️ No accounts returned from Coinbase.")
        else:
            usd_accounts = [a for a in accounts if a["currency"] == "USD"]
            crypto_accounts = [a for a in accounts if a["currency"] != "USD"]

            print("✅ Coinbase connection OK. Accounts summary:\n")

            if usd_accounts:
                for acc in usd_accounts:
                    print(f"💵 {acc['currency']}: {acc['available']} available")
            else:
                print("💵 No USD accounts found.")

            if crypto_accounts:
                for acc in crypto_accounts:
                    print(f"🪙 {acc['currency']}: {acc['available']} available")
            else:
                print("🪙 No crypto accounts found.")

    except Exception as e:
        print("❌ Coinbase connection FAILED:", e)
