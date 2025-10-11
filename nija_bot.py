#!/usr/bin/env python3
import os
import sys
import tempfile
import time
from pathlib import Path

# Helpful debug
ROOT = Path(__file__).parent.resolve()
print("🚀 nija_bot starting (robust importer)")
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:4])

# Load .env locally (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded local .env (if present)")
except Exception:
    pass

# Env vars you must set on Render
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")      # optional: full PEM contents (including header/footer & newlines)
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ WARNING: API_KEY or API_SECRET missing. Set them in Render env. Continuing only if DRY_RUN=True.")
    if not DRY_RUN:
        raise SystemExit("Missing API credentials and DRY_RUN is False")

# Import coinbase RESTClient (this is the correct import for coinbase-advanced-py==1.8.2)
try:
    import coinbase
    from coinbase.rest import RESTClient
    print("✅ Imported coinbase and RESTClient available")
except Exception as e:
    print("❌ Failed to import coinbase or RESTClient:", type(e).__name__, e)
    raise SystemExit(1)

# Validate PEM helper
def validate_pem_text(pem_text: str) -> bool:
    pem_text = pem_text.strip()
    if not (pem_text.startswith("-----BEGIN") and pem_text.endswith("-----END PRIVATE KEY-----")):
        return False
    # Basic sanity: ensure at least a few lines of base64-looking content
    inner = pem_text.splitlines()
    if len(inner) < 3:
        return False
    return True

# If API_PEM present, write to temp file after validating
pem_path = None
if API_PEM:
    if not validate_pem_text(API_PEM):
        print("❌ API_PEM appears malformed. It must start with '-----BEGIN ...' and end with '-----END PRIVATE KEY-----' and preserve newlines.")
        print("Example header/footer lines MUST be present and exact. DO NOT add extra quotes or escape characters.")
        if not DRY_RUN:
            raise SystemExit("Malformed API_PEM")
    else:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
        tmp.write(API_PEM.encode("utf-8"))
        tmp.flush()
        tmp.close()
        pem_path = tmp.name
        print("✅ Wrote API_PEM to temporary file:", pem_path)

# Instantiate RESTClient
client = None
try:
    if pem_path:
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET, private_key_file=pem_path, sandbox=SANDBOX)
    else:
        client = RESTClient(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    print("✅ RESTClient instantiated:", type(client))
except Exception as e:
    print("❌ Error instantiating RESTClient:", type(e).__name__, e)
    # If PEM issue occurs, you'll see MalformedFraming here. Keep DRY_RUN true to avoid exit.
    if not DRY_RUN:
        raise SystemExit(1)

# Safe account check (non-destructive)
def safe_accounts_check():
    try:
        if client is None:
            print("ℹ️ No client created; skipping account fetch")
            return
        if hasattr(client, "get_accounts"):
            accounts = client.get_accounts()
            print("💰 Accounts:", accounts)
        elif hasattr(client, "get_account_balances"):
            balances = client.get_account_balances()
            print("💰 Balances:", balances)
        else:
            print("ℹ️ No account methods found. Client attrs:", dir(client)[:50])
    except Exception as e:
        print("⚠️ accounts check failed:", type(e).__name__, e)

safe_accounts_check()

# Short heartbeat loop (3 iterations). For production change to while True.
for i in range(3):
    print(f"❤️ heartbeat {i+1}/3 — DRY_RUN={DRY_RUN} SANDBOX={SANDBOX}")
    time.sleep(5)

print("🛑 Demo completed. Set loop for production and set DRY_RUN=False when ready.")
