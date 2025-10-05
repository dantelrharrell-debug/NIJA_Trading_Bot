# nija_multi_trading_bot.py
import os, csv, uuid, asyncio
from datetime import datetime
from dotenv import load_dotenv
import coinbase_advanced_py as cb
import numpy as np

# -------------------
# LOAD ENV
# -------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
client = cb.Client(API_KEY, API_SECRET)

# -------------------
# SETTINGS
# -------------------
MIN_PCT = 0.02
MAX_PCT = 0.10
ACCOUNT_BALANCE = 18.07
CSV_FILE = "nija_trade_log.csv"
SYMBOLS = ["BTC-USD", "ETH-USD", "LTC-USD"]
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
                "timestamp","symbol","side","price","size","allocation_usd","risk_pct",
                "signal_type","status","notes","account_balance_after"
            ])

def compute_allocation(account_usd_balance, risk_pct):
    pct = max(MIN_PCT, min(MAX_PCT, risk_pct))
    return account_usd_balance * pct

def make_order_payload(symbol, side, account_usd_balance, price, risk_pct, signal_type):
    allocation_usd = compute_allocation(account_usd_balance, risk_pct)
    size = round(allocation_usd / price, 8)
    return {
        "product_id": symbol,
        "side": side,
        "type": "market",
        "size": str(size),
        "idempotency_key": str(uuid.uuid4()),
        "meta": {"allocation_usd": allocation_usd, "risk_pct": risk_pct, "signal_type": signal_type}
    }

def log_trade(payload, status, account_balance_after, notes=""):
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
            notes,
            round(account_balance_after,2)
        ])

# -------------------
# INDICATORS
# -------------------
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices[-(period+1):])
    ups = deltas[deltas > 0].sum() / period
    downs = -deltas[deltas < 0].sum() / period
    rs = ups / downs if downs != 0 else 0
    return 100 - (100 / (1 + rs))

def calculate_vwap(prices):
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
    vwap_dev = abs(current_price - vwap)/vwap*100
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
# ACCOUNT BALANCE UPDATE
# -------------------
def update_account_balance(trade_payload, trade_price):
    global ACCOUNT_BALANCE
    size = float(trade_payload["size"])
    side = trade_payload["side"]
    if side == "buy":
        ACCOUNT_BALANCE -= size * trade_price
    elif side == "sell":
        ACCOUNT_BALANCE += size * trade_price
    return ACCOUNT_BALANCE

# -------------------
# BOT LOOP PER SYMBOL
# -------------------
async def trade_symbol(symbol):
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
                    account_after = update_account_balance(payload, price)
                    log_trade(payload, "success", account_after)
                    print(f"✅ {symbol} | {signal_type} {signal} at ${price} size {payload['size']} | Balance: ${round(account_after,2)}")
                except Exception as e:
                    log_trade(payload, "error", ACCOUNT_BALANCE, str(e))
                    print(f"⚠️ {symbol} Trade failed:", e)

            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ {symbol} Bot error:", e)
            await asyncio.sleep(2)

# -------------------
# START MULTI-SYMBOL BOT
# -------------------
if __name__ == "__main__":
    print("🚀 Nija Multi-Symbol Compounding Bot Started!")
    asyncio.run(asyncio.gather(*(trade_symbol(sym) for sym in SYMBOLS)))
