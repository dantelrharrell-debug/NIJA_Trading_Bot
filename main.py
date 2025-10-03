# main.py
import os
from coinbase.wallet.client import Client

def test_coinbase_connection():
    try:
        client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
        account = client.get_accounts()  # Just a lightweight call
        print("✅ Coinbase connection successful!")
        print(f"First account: {account.data[0].name} | Balance: {account.data[0].balance.amount} {account.data[0].balance.currency}")
    except Exception as e:
        print(f"❌ Coinbase connection failed: {e}")

# Run the test once when the app starts
test_coinbase_connection()
import os
from fastapi import FastAPI

# ----------------------------
# Safe import for Coinbase Advanced
# ----------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Coinbase Advanced imported successfully!")
except ImportError:
    print("❌ coinbase_advanced_py NOT FOUND! Check requirements.txt and environment.")
    cb = None  # prevents crashes

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="NIJA Trading Bot API")

@app.get("/")
async def root():
    return {"status": "ok", "message": "NIJA Trading Bot is live!"}

# Example endpoint to check Coinbase connection
@app.get("/check-coinbase")
async def check_coinbase():
    if cb is None:
        return {"status": "error", "message": "Coinbase Advanced not installed."}
    
    try:
        # Example: just initialize client with dummy keys (replace with your env keys)
        api_key = os.getenv("API_KEY", "YOUR_API_KEY")
        api_secret = os.getenv("API_SECRET", "YOUR_API_SECRET")
        client = cb.Client(api_key, api_secret)
        return {"status": "ok", "message": "Coinbase client initialized!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------
# Run the app with uvicorn
# ----------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 10000))  # Render sets PORT automatically
    print(f"🚀 Starting NIJA Trading Bot on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
