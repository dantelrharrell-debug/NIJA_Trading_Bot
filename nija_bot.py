#!/usr/bin/env python3
import sys
import os

# ---------------------------
# Coinbase import check
# ---------------------------
try:
    import coinbase_advanced_py as cb
    coinbase_client = cb
    print("✅ Imported coinbase_advanced_py")
except ModuleNotFoundError as e:
    print("❌ Coinbase import failed:", e)
    coinbase_client = None  # fallback to MockClient

# ---------------------------
# Debug info
# ---------------------------
print("sys.executable:", sys.executable)
print("sys.path:", sys.path)

#!/usr/bin/env python3
import os
import sys

# ---------------------------
# Coinbase import check
# ---------------------------
try:
    import coinbase_advanced_py as cb
    coinbase_client = cb
    print("✅ Imported coinbase_advanced_py")
except ModuleNotFoundError as e:
    print("❌ Coinbase import failed:", e)
    coinbase_client = None  # fallback to mock later

# ---------------------------
# Optional: debug paths
# ---------------------------
print("sys.executable:", sys.executable)
print("sys.path:", sys.path)

# ---------------------------
# Environment / config
# ---------------------------
from dotenv import load_dotenv
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
if coinbase_client is None:
    USE_MOCK = True

# ---------------------------
# Flask setup
# ---------------------------
from flask import Flask
app = Flask(__name__)

# ... rest of your bot code ...
#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask

app = Flask(__name__)

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

coinbase_client = None

if not USE_MOCK:
    try:
        # Try the first possible import
        import coinbase_advanced_py as cb
        coinbase_client = cb
        print("✅ Imported coinbase_advanced_py")
    except ModuleNotFoundError:
        try:
            # Fallback import name
            import coinbase_advanced as cb
            coinbase_client = cb
            print("✅ Imported coinbase_advanced")
        except ModuleNotFoundError:
            print("❌ Failed to import Coinbase client, using MockClient")
            USE_MOCK = True

# -------------------
# Define a MockClient
# -------------------
class MockClient:
    def __init__(self):
        print("⚠️ MockClient initialized (no live trading)")

    def get_account(self):
        return {"balance": 0}

    def place_order(self, *args, **kwargs):
        print(f"Mock order: args={args}, kwargs={kwargs}")
        return {"id": "mock_order"}

if USE_MOCK:
    coinbase_client = MockClient()

# -------------------
# Flask server example
# -------------------
@app.route("/")
def index():
    return "NIJA Bot is running!"

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)
