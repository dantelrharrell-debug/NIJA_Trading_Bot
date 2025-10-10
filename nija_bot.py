#!/usr/bin/env python3
import os, sys, subprocess, site, time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
print("🚀 Starting Nija Trading Bot (diagnostic mode)")
print("Python:", sys.executable, sys.version.splitlines()[0])
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:6])

# show site-packages where pip installs
try:
    print("site.getsitepackages():", site.getsitepackages())
except Exception as e:
    print("site.getsitepackages() failed:", e)

# Show whether vendor exists
VENDOR_DIR = ROOT / "vendor"
print("Vendor dir exists:", VENDOR_DIR.exists(), "->", VENDOR_DIR)

# Try to import coinbase_advanced_py and if fail, print diagnostics
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("\n❌ IMPORT FAILED:", type(e).__name__, e)
    print("\n--- pip show coinbase-advanced-py ---")
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "coinbase-advanced-py"], check=False)
    except Exception as ex:
        print("pip show failed:", ex)

    print("\n--- pip list (top 80) ---")
    try:
        subprocess.run([sys.executable, "-m", "pip", "list", "--format=columns"], check=False)
    except Exception:
        pass

    print("\n--- Inspecting site-packages for coinbase_advanced_py ---")
    sp_dirs = []
    try:
        sp_dirs = site.getsitepackages()
    except Exception:
        sp_dirs = [p for p in sys.path if "site-packages" in str(p)]
    for d in sp_dirs:
        print("site-packages dir:", d)
        try:
            for p in sorted(Path(d).glob("coinbase*")):
                print("  ", p)
        except Exception:
            pass

    print("\n--- Inspecting vendor folder (if present) ---")
    if VENDOR_DIR.exists():
        for p in sorted(VENDOR_DIR.glob("*"))[:200]:
            print("  ", p)
    else:
        print("  vendor/ not present")

    # Final helpful message
    print("\n💡 Likely causes: different python interpreter used to install packages, or Render ran the bot *before* pip install completed.")
    print("Please ensure your Render Start Command is: bash start.sh")
    raise SystemExit(1)

# If import succeeded, minimal start:
from dotenv import load_dotenv
try:
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv not installed or .env not present")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1","true","yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY / API_SECRET env vars. DRY_RUN:", DRY_RUN)
    if not DRY_RUN:
        raise SystemExit("Missing keys and DRY_RUN is false. Exiting.")

# Initialize client safely
try:
    client = cb.Client(API_KEY or "fake", API_SECRET or "fake", sandbox= os.getenv("SANDBOX", "True").lower() in ("1","true","yes"))
    print("✅ Coinbase client initialized:", type(client))
except Exception as e:
    print("❌ Error initializing client:", type(e).__name__, e)
    if not DRY_RUN:
        raise SystemExit("Cannot init client and not DRY_RUN. Exiting.")

# Keep alive heartbeat so logs stream
try:
    while True:
        print("♥ Nija heartbeat — DRY_RUN=", DRY_RUN, time.strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Stopped by user")
