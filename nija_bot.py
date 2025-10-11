#!/usr/bin/env python3
# nija_bot.py — robust importer + safe Coinbase REST client instantiation
import os
import sys
import tempfile
import traceback
import time

ROOT = os.path.dirname(__file__)
print("🚀 NIJA Bot starting. Working dir:", ROOT)
print("Python executable:", sys.executable)
print("sys.path head:", sys.path[:4])

# Load .env locally if available (not needed on Render)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not available or .env missing — OK on Render")

# Environment flags
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM = os.getenv("API_PEM")  # the multiline PEM (private key)
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

print(f"DRY_RUN={DRY_RUN} SANDBOX={SANDBOX}")

# Try robust import for the installed Coinbase package
client = None
pem_temp_path = None

try:
    # Many installs expose a top-level 'coinbase' package (this was shown in your logs)
    import coinbase
    print("✅ Imported top-level 'coinbase' module:", getattr(coinbase, "__file__", None))
except Exception as e:
    print("❌ Could not import 'coinbase':", type(e).__name__, e)
    traceback.print_exc()
    if not DRY_RUN:
        raise SystemExit(1)

# The REST client class is at coinbase.rest.RESTClient in the installed distribution
try:
    from coinbase.rest import RESTClient as RESTClient
    print("✅ Found RESTClient at coinbase.rest.RESTClient")
except Exception as e:
    print("❌ RESTClient not found in coinbase.rest:", type(e).__name__, e)
    traceback.print_exc()
    if not DRY_RUN:
        raise SystemExit(1)
    RESTClient = None

# If API_PEM provided, write to temp file (preserve newlines exactly)
if API_PEM:
    try:
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM.encode("utf-8"))
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote API_PEM to temporary file:", pem_temp_path)
    except Exception as e:
        print("❌ Failed to write API_PEM to temporary file:", e)
        traceback.print_exc()
        pem_temp_path = None

# Instantiate client — the correct parameter name from the logs is 'key_file'
if RESTClient:
    try:
        if pem_temp_path:
            client = RESTClient(api_key=API_KEY, api_secret=API_SECRET, key_file=pem_temp_path)
            print("✅ RESTClient instantiated with key_file (temp PEM)")
        else:
            client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
            print("✅ RESTClient instantiated without key_file (no PEM provided)")
    except Exception as e:
        print("❌ Error instantiating RESTClient:", type(e).__name__, e)
        traceback.print_exc()
        # If this is a PEM-format failure, print hint and continue when DRY_RUN
        if "MalformedFraming" in str(e) or "Unable to load PEM" in str(e) or "load_pem" in str(e):
            print("⚠️ PEM-load error. Your API_PEM is likely malformed or not the private key provided by Coinbase Cloud.")
        if not DRY_RUN:
            raise SystemExit(1)
else:
    print("❌ RESTClient class not available. Cannot continue.")
    if not DRY_RUN:
        raise SystemExit(1)

# Optional: quick safe accounts check (read-only)
def safe_accounts_check():
    if client is None:
        print("ℹ️ No client available for accounts check.")
        return
    try:
        # library may expose get_accounts() or get_account_balances(); try both safely
        if hasattr(client, "get_accounts"):
            print("ℹ️ Calling client.get_accounts() (read-only)...")
            accounts = client.get_accounts()
            print("💰 Accounts (preview):", accounts if isinstance(accounts, list) else str(accounts)[:500])
        elif hasattr(client, "get_account_balances"):
            print("ℹ️ Calling client.get_account_balances() (read-only)...")
            balances = client.get_account_balances()
            print("💰 Balances (preview):", balances)
        else:
            print("ℹ️ No account listing method found on client. Methods:", dir(client)[:60])
    except Exception as e:
        print("⚠️ accounts check failed:", type(e).__name__, e)
        traceback.print_exc()
        # If PEM is bad, cryptography throws errors — do not exit if we're in DRY_RUN
        if not DRY_RUN:
            raise

# Run a safe check and then enter minimal loop
safe_accounts_check()

print("✅ Startup complete. Entering main loop (heartbeat).")
try:
    while True:
        print(f"💓 heartbeat — DRY_RUN={DRY_RUN} (time: {time.strftime('%Y-%m-%d %H:%M:%S')})")
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Stopping by KeyboardInterrupt")

# Clean up temp PEM file on shutdown (best-effort)
if pem_temp_path:
    try:
        os.unlink(pem_temp_path)
        print("✅ Removed temp PEM:", pem_temp_path)
    except Exception:
        pass
