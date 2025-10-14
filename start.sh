#!/usr/bin/env python3
import os
import traceback
from flask import Flask

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")
        # Optional: initialize client if API keys present
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        if not API_KEY or not API_SECRET:
            print("⚠️ API_KEY or API_SECRET not found in environment — switching to mock mode.")
            USE_MOCK = True
        else:
            try:
                client = cb.Client(API_KEY, API_SECRET)
                print("🚀 Coinbase client initialized.")
            except Exception as e:
                print("❌ Failed to initialize Coinbase client:", e)
                USE_MOCK = True
    except Exception as e:
        print("❌ coinbase_advanced_py not found or import failed:", e)
        USE_MOCK = True
else:
    print("⚠️ Running in mock mode — Coinbase client not connected.")

# Now the rest of your app can check USE_MOCK variable
# e.g., if USE_MOCK: use_mock_client() else: use real client
