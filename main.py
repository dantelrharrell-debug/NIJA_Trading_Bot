# ------------------------------
# Nija Bot Live Deployment Version - Webhook Driven Trading
# ------------------------------

import os
import time
import threading
from datetime import datetime, timezone
from coinbase.wallet.client import Client
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# ------------------------------
# Load environment variables
# ------------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # set this in your .env and TradingView webhook body/header

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET not found. Please set them in your .env file.")
if not WEBHOOK_SECRET:
    print("⚠️ WEBHOOK_SECRET not set. Incoming webhooks will be rejected unless you set this in .env.")

# ------------------------------
# Initialize Coinbase client
# ------------------------------
client = Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized successfully!")

# ------------------------------
# Minimum trade amounts per ticker (USD equivalents)
# ------------------------------
coinbase_min = {
    "BTC-USD": 10,
    "ETH-USD": 1,
    "LTC-USD": 1,
    "SOL-USD": 1,
    "DOGE-USD": 1,
    "XRP-USD": 1,
}

priority_order = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD", "DOGE-USD", "XRP-USD"]

# ------------------------------
# In-memory signal store (thread-safe)
# ------------------------------
signals_lock = threading.Lock()
# signals structure: { "BTC-USD": {"action":"buy", "ts": 169xxx, "meta": {...}} }
signals = {}

# How long a signal stays valid (seconds) before ignored
SIGNAL_TTL = 60 * 10  # 10 minutes (tweak as needed)

# ------------------------------
# Balance & allocation helpers (same as before)
# ------------------------------
def allocate_dynamic(balance_fetcher, min_trade, priority):
    total_balance = balance_fetcher()
    allocations = {asset: 0 for asset in min_trade.keys()}
    
    for asset in priority:
        if total_balance >= min_trade[asset]:
            allocations[asset] = min_trade[asset]
            total_balance -= min_trade[asset]

    funded = [a for a, amt in allocations.items() if amt >= min_trade[a]]
    if funded and total_balance > 0:
        per_asset_extra = total_balance / len(funded)
        for a in funded:
            allocations[a] += per_asset_extra

    for a in allocations:
        if 0 < allocations[a] < min_trade[a]:
            allocations[a] = 0

    return allocations

def get_current_balance():
    try:
        account = client.get_account("USD")
        return float(account.balance.amount)
    except Exception as e:
        print(f"Error fetching USD balance: {e}")
        return 0

# ------------------------------
# Coinbase balance + price helpers
# ------------------------------
def get_coin_balance(coin):
    """
    coin is like 'BTC' or 'ETH' — uses client.get_account with currency code.
    Note: coinbase.wallet.Client.get_account expects account id or currency?
    If your client requires a different call, adapt accordingly.
    """
    try:
        acct = client.get_account(coin)
        return float(acct.balance.amount)
    except Exception:
        return None

def get_usd_value(coin, bal):
    """
    Use client.get_spot_price to get price; returns USD value or None.
    """
    try:
        spot = client.get_spot_price(currency_pair=f"{coin}-USD")
        price = float(spot.amount)
        return bal * price
    except Exception:
        return None

# ------------------------------
# Dashboard printer
# ------------------------------
def print_balances_dashboard():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print("\033c", end="")  # clear terminal (best-effort)
    print(f"NIJA BOT — Balance Dashboard — {timestamp}")
    print("-" * 80)

    usd = get_current_balance()
    print(f"{'USD':6} | ${usd:,.2f} | Signals queued: {len(signals)}")
    print("-" * 80)

    eligible_count = 0
    for coin in ["BTC", "ETH", "LTC", "SOL", "DOGE", "XRP"]:
        bal = get_coin_balance(coin)
        if bal is None:
            print(f"{coin:6} | API ERROR")
            continue
        usd_val = get_usd_value(coin, bal)
        if usd_val is None:
            print(f"{coin:6} | {bal:.6f} | USD Val: API ERROR")
            continue
        meets = "YES ✅" if usd_val >= coinbase_min[f"{coin}-USD"] else "NO ⏭"
        if usd_val >= coinbase_min[f"{coin}-USD"]:
            eligible_count += 1
        print(f"{coin:6} | {bal:.6f} | ${usd_val:,.2f} | Eligible: {meets}")

    print("-" * 80)
    print(f"Eligible for trading: {eligible_count}/{len(coinbase_min)}")
    print("\n")

# ------------------------------
# Trade execution
# ------------------------------
def execute_trade(asset, side="buy"):
    """
    asset format: 'BTC-USD' etc. Uses dynamic allocation to determine trade size.
    """
    dynamic_allocations = allocate_dynamic(get_current_balance, coinbase_min, priority_order)
    trade_amount = dynamic_allocations.get(asset, 0)
    
    if trade_amount <= 0:
        print(f"Skipped {asset}: allocation below minimum.")
        return False

    try:
        # Coinbase wallet Client.place_order may differ; adapt arguments to your library version.
        order = client.place_order(
            product_id=asset,
            side=side,
            order_type="market",
            size=str(trade_amount)  # some SDKs expect string amounts
        )
        print(f"✅ Placed {side} order for {asset} with amount ${trade_amount}")
        return True
    except Exception as e:
        print(f"❌ Error placing order for {asset}: {e}")
        return False

# ------------------------------
# FastAPI webhook endpoint
# ------------------------------
app = FastAPI()

def verify_webhook_secret(provided_secret: str):
    if not WEBHOOK_SECRET:
        # If you don't set WEBHOOK_SECRET, reject for safety
        return False
    return provided_secret == WEBHOOK_SECRET

@app.post("/webhook")
async def webhook(request: Request):
    """
    Expected JSON examples:
    1) Simple:
       { "asset": "BTC-USD", "action": "buy", "secret": "mysecret" }
    2) TradingView custom message:
       { "ticker": "BTCUSD", "strategy": {"order_action":"buy"}, "secret":"..." }
    This endpoint is intentionally permissive about field names.
    """
    payload = await request.json()
    # Attempt to extract secret (try header first then payload)
    provided_secret = request.headers.get("X-WEBHOOK-SECRET") or payload.get("secret") or payload.get("password")
    if not verify_webhook_secret(provided_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    # normalize action and asset
    action = None
    asset = None

    # Try common fields
    if "action" in payload:
        action = payload.get("action")
    if "order" in payload:
        action = payload.get("order")
    # tradingview common: strategy.order.action or strategy.order.action
    if payload.get("strategy") and isinstance(payload.get("strategy"), dict):
        # adapt to common TradingView shapes
        sv = payload["strategy"]
        action = action or sv.get("order_action") or sv.get("order_action_lower") or sv.get("order")
    
    # asset/ticker extraction
    asset = payload.get("asset") or payload.get("ticker") or payload.get("symbol")
    # Normalize ticker like BTCUSD -> BTC-USD
    if asset and isinstance(asset, str):
        asset = asset.upper().replace("USD", "-USD").replace("_", "-").replace("/", "-")
        # quick mapping if user sent BTCUSD or BTC/USD
        if asset.endswith("-USD") is False and asset.endswith("USD"):
            asset = asset.replace("USD", "-USD")

    # Last attempt: maybe payload had a message string
    if not action and "message" in payload and isinstance(payload["message"], str):
        if "buy" in payload["message"].lower():
            action = "buy"
        elif "sell" in payload["message"].lower():
            action = "sell"

    if not asset or not action:
        raise HTTPException(status_code=400, detail="Webhook JSON must include asset and action (buy/sell)")

    action = action.lower()
    if action not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="action must be 'buy' or 'sell'")

    # Store signal (thread-safe)
    with signals_lock:
        signals[asset] = {"action": action, "ts": time.time(), "payload": payload}

    print(f"🔔 Received webhook: {asset} -> {action}")
    return {"status": "accepted", "asset": asset, "action": action}

# ------------------------------
# Background: main trading loop (runs in separate thread)
# ------------------------------
def trading_loop():
    assets_to_trade = list(coinbase_min.keys())

    while True:
        try:
            # 1) show balances dashboard
            print_balances_dashboard()

            # 2) process each signal (copy to avoid holding lock during trades)
            with signals_lock:
                current_signals = dict(signals)

            for asset, sig in current_signals.items():
                # validate TTL
                age = time.time() - sig["ts"]
                if age > SIGNAL_TTL:
                    # stale -> drop
                    with signals_lock:
                        signals.pop(asset, None)
                    print(f"Signal for {asset} expired (age {age:.1f}s). Dropped.")
                    continue

                # Ensure asset is supported and formatted like 'BTC-USD'
                if asset not in assets_to_trade:
                    print(f"Unsupported asset in signal: {asset} — ignoring.")
                    with signals_lock:
                        signals.pop(asset, None)
                    continue

                # Execute the trade
                success = execute_trade(asset, side=sig["action"])
                # After executing once, remove the signal to avoid duplicate trades.
                with signals_lock:
                    signals.pop(asset, None)

                # Optionally: if trade failed, you could requeue or alert
                time.sleep(1)  # small pause between trades

        except Exception as e:
            print(f"Trading loop error: {e}")

        # Sleep until next cycle
        print("Waiting 60 seconds for next trading cycle...")
        time.sleep(60)

# ------------------------------
# Start server + trading loop
# ------------------------------
if __name__ == "__main__":
    # Start trading loop in background thread
    thread = threading.Thread(target=trading_loop, daemon=True)
    thread.start()

    # Start FastAPI server (listens for webhooks)
    # In production, run uvicorn via command line with workers (uvicorn main:app --host 0.0.0.0 --port 8000)
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
