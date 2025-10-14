#!/usr/bin/env python3
import os
import sys
import importlib.util
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
print("✅ API_KEY and API_SECRET loaded:", bool(API_KEY), bool(API_SECRET))

# Diagnostics to confirm which Python and site-packages are used
print("Python executable:", sys.executable)
print("sys.path (first 6):", sys.path[:6])

# Try correct import used by coinbase-advanced-py
try:
    from coinbase.rest import RESTClient
    print("✅ coinbase (coinbase-advanced-py) import successful: from coinbase.rest import RESTClient")
except ModuleNotFoundError as exc:
    print("❌ coinbase NOT found. ModuleNotFoundError:", exc)
    print("importlib.util.find_spec('coinbase'):", importlib.util.find_spec("coinbase"))
    # Fail fast during deploy if you want to stop startup when missing:
    sys.exit(1)

# (Optional) quick sanity: check unexpected package name
try:
    import coinbase_advanced_py
    print("⚠️  coinbase_advanced_py unexpectedly present")
except ModuleNotFoundError:
    print("ℹ️  coinbase_advanced_py not present (expected)")

#!/usr/bin/env python3
import os
import sys
import importlib.util
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
print("✅ API_KEY and API_SECRET loaded:", bool(API_KEY), bool(API_SECRET))

# Diagnostics to confirm which Python and site-packages are used
print("Python executable:", sys.executable)
print("sys.path (first 6):", sys.path[:6])

# Try correct import used by coinbase-advanced-py
try:
    from coinbase.rest import RESTClient
    print("✅ coinbase (coinbase-advanced-py) import successful: from coinbase.rest import RESTClient")
except ModuleNotFoundError as exc:
    print("❌ coinbase NOT found. ModuleNotFoundError:", exc)
    print("importlib.util.find_spec('coinbase'):", importlib.util.find_spec("coinbase"))
    # Fail fast during deploy if you want to stop startup when missing:
    sys.exit(1)

# (Optional) quick sanity: check unexpected package name
try:
    import coinbase_advanced_py
    print("⚠️  coinbase_advanced_py unexpectedly present")
except ModuleNotFoundError:
    print("ℹ️  coinbase_advanced_py not present (expected)")
