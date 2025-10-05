# nija_trading_bot.py
import os, time, csv, uuid, asyncio
from datetime import datetime
from dotenv import load_dotenv
import coinbase_advanced_py as cb  # adapt if different

# -------------------
# LOAD ENV
# -------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = cb.Client(API_KEY, API_SECRET)  # sync client; adapt if using async

# -------------------
# ACCOUNT / ALLOCATION SETTINGS
# -------------------
MIN_PCT = 0.02  # 2%
MAX_PCT = 0.10  # 10%
ACCOUNT_BALANCE = 18.07  # your starting account balance, will auto-update per trade

CSV_FILE = "nija_trade_log.csv"

# -------------------
# UTILITY FUNCTIONS
# -------------------
def now_ts():
    return datetime.utcnow().isoformat() + "Z"

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp","symbol","side","price","size","allocation_usd","risk_pct","signal_type","status","notes"
            ])

def compute_allocation_from_equity(account_usd_balance: float, risk_pct: float) -> float:
    pct = max(MIN_PCT, min(MAX_PCT, float(risk_pct)))
    allocation_usd = account_usd_balance * pct
    return allocation_usd

def make_order_payload(symbol: str, side: str, account_usd_balance: float, price: float, risk_pct: float, signal_type:str):
    allocation_usd = compute_allocation_from_equity(account_usd_balance, risk_pct)
    size = round(allocation_usd / price, 8)
    idempotency_key = str(uuid.uuid4())
    payload = {
        "product_id": symbol,
        "side": side,
        "type": "market",
        "size": str(size),
        "idempotency_key": idempotency_key,
        "meta": {"allocation_usd": allocation_usd, "risk_pct": risk_pct, "signal_type": signal_type}
    }
    return payload

def log_trade(payload, status, notes=""):
    ensure_csv()
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            now_ts(),
            payload["product_id"],
            payload["side"],
            "LIVE" if status=="success" else "",
            payload["size"],
            payload["meta"]["allocation_usd"],
            payload["meta"]["risk_pct"],
            payload["meta"]["signal_type"],
            status,
            notes
        ])

# -------------------
# SIGNAL LOGIC
# -------------------
def hf_micro_trade_signal(price_data):
    """HFMT: micro-trade dip / rise strategy"""
    if len(price_data) < 2:
        return None
    last_price = price_data[-2]
    current_price = price_data[-1]
    if current_price <= last_price * 0.998:
        return "buy"
    elif current_price >= last_price * 1.003:
        return "sell"
    return None

def high_return_signal(rsi, vwap_deviation):
    """High-return signal: RSI + VWAP"""
    base_risk = 0.04
    adjustment = 0
    if rsi < 30:
        adjustment += 0.03
    if vwap_deviation > 0.5:
        adjustment += 0.03
    risk_pct = max(MIN_PCT, min(MAX_PCT, base_risk + adjustment))
    side = "buy" if rsi < 30 else "sell"
    return side, risk_pct

# -------------------
# MAIN BOT LOOP
# -------------------
async def run_bot(symbol="BTC-USD"):
    price_data = []
    while True:
        try:
            ticker = client.get_ticker(symbol)  # live price
            price = float(ticker["price"])
            price_data.append(price)
            if len(price_data) > 100:  # keep last 100 ticks
                price_data.pop(0)
            
            # HFMT signal
            signal = hf_micro_trade_signal(price_data)
            risk_pct = MIN_PCT
            signal_type = "HFMT"

            # If no HFMT signal, check high-return
            if not signal:
                # Example indicators: placeholder values; replace with real RSI/VWAP
                rsi = 25  # simulated
                vwap_dev = 0.6  # simulated
                signal, risk_pct = high_return_signal(rsi, vwap_dev)
                signal_type = "HighReturn"

            if signal:
                payload = make_order_payload(symbol, signal, ACCOUNT_BALANCE, price, risk_pct, signal_type)
                try:
                    resp = client.place_market_order(payload)  # live trade
                    log_trade(payload, "success")
                    print(f"✅ Executed {signal_type} {signal} order at ${price} size {payload['size']}")
                except Exception as e:
                    log_trade(payload, "error", str(e))
                    print("⚠️ Trade failed:", e)

            await asyncio.sleep(1)  # 1-second micro-trade frequency; adjust if needed
        except Exception as e:
            print("⚠️ Bot error:", e)
            await asyncio.sleep(2)

# -------------------
# START
# -------------------
if __name__ == "__main__":
    print("🚀 Nija Trading Bot Started!")
    asyncio.run(run_bot())
