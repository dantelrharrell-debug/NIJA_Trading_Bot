#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv
import coinbase_advanced_py as cb

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

accounts = cb.get_accounts(api_key=API_KEY, api_secret=API_SECRET)
print("💰 Accounts:", accounts)

while True:
    print(f"✅ Nija bot heartbeat — DRY_RUN={DRY_RUN}")
    time.sleep(30)
