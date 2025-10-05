# nija_trading_bot_realtime.py
import os, csv, uuid, asyncio
from datetime import datetime
from dotenv import load_dotenv
import coinbase_advanced_py as cb  # adapt if different
import numpy as np

# -------------------
# LOAD ENV
# -------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
client = cb.Client(API_KEY, API_SECRET)  # adapt to async if available

# -------------------
# SETTINGS
# -------------------
MIN_PCT = 0.02
MAX_PCT = 0.10
ACCOUNT_BALANCE = 18.07
CSV_FILE = "nija_trade_log.csv"
SYMBOL = "BTC-USD"
RSI_PERIOD = 14
VWAP_PERIOD = 20

# -------------------
# UTILITY
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

def compute_allocation_from_equity(account_usd_balance, risk_pct):
    pct = max(MIN_PCT, min(MAX_PCT, risk_pct))
    return account_usd_balance * pct

def make_order_payload(symbol, side, account_usd_balance, price, risk_pct, signal_type):
    allocation_usd = compute_allocation_from_equity(account_usd_balance, risk_pct)
    size = round(allocation_usd / price, 8)
    payload = {
        "product_id": symbol,
        "side": side,
        "type": "market",
        "size": str(size),
        "idempotency_key": str(uuid.uuid4()),
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
# INDICATORS
# -------------------
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50  # neutral
    deltas = np.diff(prices[-(period+1):])
    ups = deltas[deltas > 0].sum() / period
    downs = -deltas[deltas < 0].sum() / period
    rs = ups / downs if downs != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_vwap(prices):
    # simple VWAP using prices as volume-weighted (assume volume=1 for simplicity)
    return np.mean(prices[-VWAP_PERIOD:]) if len(prices) >= VWAP_PERIOD else np.mean(prices)

# -------------------
# SIGNAL LOGIC
# -------------------
def hf_micro_trade_signal(price_data):
    if len(price_data) < 2:
        return None
    last_price = price_data[-2]
    current_price = price_data[-1]
    if current_price <= last_price * 0.998:
        return "buy"
    elif current_price >= last_price * 1.003:
        return "sell"
    return None

def high_return_signal(price_data):
    rsi = calculate_rsi(price_data, RSI_PERIOD)
    vwap = calculate_vwap(price_data)
    current_price = price_data[-1]
    vwap_dev = abs(current_price - vwap) / vwap * 100  # percent deviation
    base_risk = 0.04
    adjustment = 0
    side = None
    if rsi < 30:
        adjustment += 0.03
        side = "buy"
    elif rsi > 70:
        adjustment += 0.03
        side = "sell"
    if vwap_dev > 0.5:
        adjustment += 0.03
    risk_pct = max(MIN_PCT, min(MAX_PCT, base_risk + adjustment))
    return side, risk_pct

# -------------------
# MAIN LOOP
# -------------------
async def run_bot(symbol=SYMBOL):
    price_data = []
    while True:
        try:
            ticker = client.get_ticker(symbol)
            price = float(ticker["price"])
            price_data.append(price)
            if len(price_data) > 100:
                price_data.pop(0)

            # HFMT
            signal = hf_micro_trade_signal(price_data)
            risk_pct = MIN_PCT
            signal_type = "HFMT"

            # High-return if HFMT not triggered
            if not signal:
                signal, risk_pct = high_return_signal(price_data)
                signal_type = "HighReturn"

            if signal:
                payload = make_order_payload(symbol, signal, ACCOUNT_BALANCE, price, risk_pct, signal_type)
                try:
                    resp = client.place_market_order(payload)
                    log_trade(payload, "success")
                    print(f"✅ Executed {signal_type} {signal} at ${price} size {payload['size']}")
                except Exception as e:
                    log_trade(payload, "error", str(e))
                    print("⚠️ Trade failed:", e)

            await asyncio.sleep(1)  # adjust frequency
        except Exception as e:
            print("⚠️ Bot error:", e)
            await asyncio.sleep(2)

# -------------------
# START
# -------------------
if __name__ == "__main__":
    print("🚀 Nija Real-Time Trading Bot Started!")
    asyncio.run(run_bot())
