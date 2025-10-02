import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn

load_dotenv()

# --- Coinbase Client Setup ---
client = None
try:
    from coinbase.wallet.client import Client
    client = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    print("Client initialized: coinbase.wallet.Client")
except Exception as e:
    print("coinbase.wallet.Client import failed, trying advanced client...")
    try:
        import coinbase_advanced_py as cbadv
        client = cbadv.Client(api_key=os.getenv("API_KEY"), api_secret=os.getenv("API_SECRET"))
        print("Client initialized: coinbase_advanced_py.Client")
    except Exception as e:
        print("Failed to initialize any Coinbase client:", e)
        traceback.print_exc()

# --- Account Fetching ---
def fetch_usd_balance():
    if not client:
        print("Client not initialized, returning USD balance = 0")
        return 0
    try:
        if hasattr(client, 'get_accounts'):
            accounts = client.get_accounts()
            for acc in accounts['data']:
                if acc['currency'] == 'USD':
                    return float(acc['balance']['amount'])
        else:
            accounts = client.get_accounts()
            for acc in accounts:
                if acc['currency'] == 'USD':
                    return float(acc['balance'])
    except Exception as e:
        print("Error fetching USD balance:", e)
        traceback.print_exc()
    return 0

# --- FastAPI Setup ---
app = FastAPI()
minimum_allocation = 10  # USD

@app.post("/webhook")
async def webhook_listener(req: Request):
    try:
        data = await req.json()
        print("Webhook received:", data)

        pair = data.get("pair")
        allocation_percent = data.get("allocation_percent", 10)  # Default 10%
        action = data.get("strategy", "").lower()  # "buy" or "sell"

        if action not in ["buy", "sell"]:
            return {"status": "skipped", "reason": "Invalid action"}

        usd_balance = fetch_usd_balance()
        allocation = usd_balance * (allocation_percent / 100)

        if allocation < minimum_allocation:
            return {"status": "skipped", "reason": f"Allocation below minimum for {pair}"}

        # --- Place trade logic ---
        print(f"{action.upper()} trade for {pair} with allocation ${allocation:.2f}")

        # Example: replace with your actual trade placement code
        # if action == "buy":
        #     client.place_order(pair, allocation, order_type="market", side="buy")
        # elif action == "sell":
        #     client.place_order(pair, allocation, order_type="market", side="sell")

        return {"status": "success", "pair": pair, "action": action, "allocation": allocation}

    except Exception as e:
        print("Error handling webhook:", e)
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# --- Run Server ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
