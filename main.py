"""
main.py - Nija Trading Bot (editor-safe single file)
Paste this into main.py in the Replit editor (NOT the shell).
"""

# --------------------------
# Imports & logging (paste chunk 1 if iPad)
# --------------------------
import sys
import logging
from flask import Flask, render_template_string, jsonify
import threading
import time
import traceback
import json
import os
from collections import deque
from datetime import datetime, timezone

# Setup logging to stdout + file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", mode="a")
    ]
)
log = logging.getLogger("nija")

# Replace this with your actual Nija API module import
import nija  # ensure this module exists in your Replit environment

# --------------------------
# Config (paste chunk 2 if iPad)
# --------------------------
# Risk settings
MAX_RISK_PER_TRADE = 10.0
MIN_RISK_PERCENT = 2.0
MAX_RISK_PERCENT = 10.0

# Polling / frequency
LOOP_SLEEP = 0.5                 # seconds between cycles (adjustable)
MIN_TIME_BETWEEN_TRADES = 0.2

# Trailing settings (base)
BASE_TRAILING_STOP_LOSS = 0.10
BASE_TRAILING_TAKE_PROFIT = 0.20
VOLATILITY_MULTIPLIER = 1.5

# Safety / circuit-breaker
MAX_DRAWDOWN_PERCENT = 30.0
CIRCUIT_BREAKER_PAUSE = 3600

MIN_POSITION_SIZE = 0.000001
BASE_BACKOFF = 1.0
MAX_BACKOFF = 60.0
PAPER_MODE = False  # Set True to simulate (no live order placement)

# Files & stats
TRADE_LOG_FILE = "trades.log"
TRADE_CSV_FILE = "trades.csv"
_trade_timestamps = deque()
_total_trades = 0

dashboard_data = {
    "account_balance": 0.0,
    "last_trade": None,
    "last_signal": None,
    "trailing_stop": 0.0,
    "trailing_take_profit": 0.0,
    "heartbeat": "Offline",
    "status_notes": ""
}

# Runtime state
_initial_balance = None
_peak_balance = None
_backoff_sleep = BASE_BACKOFF
_last_trade_time = 0
_open_positions = []
_circuit_breaker_triggered_at = None

# --------------------------
# Safe API wrappers & helpers
# --------------------------
def safe_get_account_balance():
    try:
        return float(nija.get_account_balance())
    except Exception as e:
        log.warning(f"get_account_balance failed: {e}")
        return 0.0

def safe_get_price():
    try:
        return float(nija.get_price())
    except Exception as e:
        log.warning(f"get_price failed: {e}")
        return None

def safe_get_signal():
    try:
        return nija.get_signal()
    except Exception as e:
        log.warning(f"get_signal failed: {e}")
        return None

def safe_get_stop_distance(price):
    try:
        return float(nija.get_stop_distance(price))
    except Exception as e:
        log.warning(f"get_stop_distance failed: {e}")
        return None

def safe_get_ATR():
    try:
        atr = nija.get_ATR()
        return float(atr) if atr is not None else 0.0
    except Exception as e:
        log.warning(f"get_ATR failed: {e}")
        return 0.0

# --------------------------
# Risk & sizing
# --------------------------
def calculate_risk(account_balance):
    min_r = account_balance * (MIN_RISK_PERCENT / 100.0)
    max_r = account_balance * (MAX_RISK_PERCENT / 100.0)
    return max(min_r, min(max_r, MAX_RISK_PER_TRADE))

def calculate_position_size(entry_price, stop_loss_distance, account_balance):
    if stop_loss_distance is None or stop_loss_distance <= 0:
        stop_loss_distance = 0.01
    risk_amount = calculate_risk(account_balance)
    if risk_amount < 0.01:
        return 0.0, risk_amount
    size = risk_amount / stop_loss_distance
    if size < MIN_POSITION_SIZE:
        return 0.0, risk_amount
    return size, risk_amount

# --------------------------
# Volatility-adjusted trailing
# --------------------------
def calculate_volatility_adjusted_levels(entry_price):
    atr = safe_get_ATR()
    tsl_percent = BASE_TRAILING_STOP_LOSS * (1 + VOLATILITY_MULTIPLIER * abs(atr))
    ttp_percent = BASE_TRAILING_TAKE_PROFIT * (1 + VOLATILITY_MULTIPLIER * abs(atr))
    trailing_stop_loss = entry_price * (1 - tsl_percent)
    trailing_take_profit = entry_price * (1 + ttp_percent)
    return trailing_stop_loss, trailing_take_profit, tsl_percent, ttp_percent

# --------------------------
# Circuit-breaker
# --------------------------
def update_balance_tracking(curr_balance):
    global _initial_balance, _peak_balance, _circuit_breaker_triggered_at
    if _initial_balance is None:
        _initial_balance = curr_balance
        _peak_balance = curr_balance
    if curr_balance > _peak_balance:
        _peak_balance = curr_balance
    drawdown = 0.0
    if _peak_balance and _peak_balance > 0:
        drawdown = ((_peak_balance - curr_balance) / _peak_balance) * 100.0
    if drawdown >= MAX_DRAWDOWN_PERCENT:
        if _circuit_breaker_triggered_at is None:
            _circuit_breaker_triggered_at = time.time()
            dashboard_data["status_notes"] = f"CIRCUIT BREAKER TRIPPED: drawdown {drawdown:.2f}%"
            log.warning(dashboard_data["status_notes"])
        return True
    return False

def circuit_breaker_active():
    global _circuit_breaker_triggered_at
    if _circuit_breaker_triggered_at is None:
        return False
    elapsed = time.time() - _circuit_breaker_triggered_at
    if elapsed > CIRCUIT_BREAKER_PAUSE:
        _circuit_breaker_triggered_at = None
        dashboard_data["status_notes"] = ""
        return False
    return True

# --------------------------
# Logging & trade file helpers
# --------------------------
def _append_trade_log(record: dict):
    try:
        with open(TRADE_LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        log.warning(f"failed to write trade log: {e}")
    try:
        header = not os.path.exists(TRADE_CSV_FILE)
        with open(TRADE_CSV_FILE, "a") as f:
            if header:
                f.write("ts,iso,side,entry,size,risk\n")
            f.write(f"{record['ts']},{record['iso']},{record['side']},{record['entry']},{record['size']},{record['risk']}\n")
    except Exception as e:
        log.warning(f"failed to write trade csv: {e}")

# --------------------------
# Place trade with backoff
# --------------------------
def place_trade_with_backoff(entry_price, size, side, trailing_stop, trailing_take_profit, risk_amount):
    global _backoff_sleep
    attempt = 0
    while True:
        attempt += 1
        try:
            if PAPER_MODE:
                fake_result = {"success": True, "id": f"paper_{int(time.time())}"}
                log.info(f"[PAPER] Simulated place_trade: {fake_result}")
                _backoff_sleep = BASE_BACKOFF
                return {"success": True, "result": fake_result}
            result = nija.place_trade(
                entry_price=entry_price,
                size=size,
                side=side,
                trailing_stop=trailing_stop,
                trailing_take_profit=trailing_take_profit
            )
            _backoff_sleep = BASE_BACKOFF
            return {"success": True, "result": result}
        except Exception as e:
            err_text = str(e)
            log.error(f"place_trade exception (attempt {attempt}): {err_text}")
            traceback.print_exc()
            time.sleep(_backoff_sleep)
            _backoff_sleep = min(_backoff_sleep * 2.0, MAX_BACKOFF)
            continue

# --------------------------
# open_trade with logging + stats (paste chunk 3 if iPad)
# --------------------------
def open_trade(entry_price, stop_loss_distance, side="BUY"):
    global _last_trade_time, _open_positions, _trade_timestamps, _total_trades
    balance = safe_get_account_balance()
    if update_balance_tracking(balance):
        log.warning("Circuit breaker active — skipping trade.")
        return {"success": False, "reason": "circuit-breaker"}

    size, risk_amount = calculate_position_size(entry_price, stop_loss_distance, balance)
    if size <= 0:
        log.info(f"[SKIP] size too small or risk too low. size={size}, risk_amount={risk_amount:.4f}")
        return {"success": False, "reason": "size-too-small", "size": size, "risk": risk_amount}

    trailing_stop, trailing_take_profit, tsl_pct, ttp_pct = calculate_volatility_adjusted_levels(entry_price)

    cumulative_risk = sum([p.get("risk",0) for p in _open_positions])
    if cumulative_risk + risk_amount > safe_get_account_balance():
        log.info("[SKIP] cumulative risk would exceed account balance, skipping trade.")
        return {"success": False, "reason": "cumulative-risk-exceeded"}

    res = place_trade_with_backoff(entry_price, size, side, trailing_stop, trailing_take_profit, risk_amount)
    if res.get("success"):
        _open_positions.append({"size": size, "risk": risk_amount, "entry": entry_price, "side": side, "ts": time.time()})
        _last_trade_time = time.time()

        dashboard_data.update({
            "account_balance": balance,
            "last_trade": f"{side} @ ${entry_price:.2f} ({size:.6f} units, Risk ${risk_amount:.2f})",
            "last_signal": side,
            "trailing_stop": trailing_stop,
            "trailing_take_profit": trailing_take_profit,
            "heartbeat": "Online ✅",
            "status_notes": ""
        })

        now_ts = int(time.time())
        iso_ts = datetime.now(timezone.utc).isoformat()
        record = {
            "ts": now_ts,
            "iso": iso_ts,
            "side": side,
            "entry": entry_price,
            "size": float(size),
            "risk": float(risk_amount),
            "trailing_stop": trailing_stop,
            "trailing_take_profit": trailing_take_profit
        }
        _append_trade_log(record)
        _trade_timestamps.append(now_ts)
        _total_trades += 1
        while len(_trade_timestamps) > 10000:
            _trade_timestamps.popleft()

        log.info(f"[{side} TRADE] Entry: ${entry_price:.2f}, Size: {size:.6f}, Risk: ${risk_amount:.2f}, TSL%:{tsl_pct:.4f}, TTP%:{ttp_pct:.4f}")
        return {"success": True, "result": res.get("result")}
    else:
        log.error(f"[FAIL] place_trade failed: {res}")
        return {"success": False, "result": res}

# --------------------------
# Main loop (high-frequency + persistent heartbeat)
# --------------------------
def live_trading_loop():
    global _last_trade_time
    log.info("Nija Trading Bot is live ✅ (high-frequency mode)")
    last_signal_time = 0
    while True:
        try:
            if circuit_breaker_active():
                log.warning("[CIRCUIT] Trading paused due to circuit-breaker. Waiting...")
                dashboard_data["heartbeat"] = "Paused (circuit-breaker)"
                time.sleep(5)
                continue

            t0 = time.time()
            signal = safe_get_signal()                # BUY / SELL / None
            price = safe_get_price()
            stop_distance = safe_get_stop_distance(price)

            log.debug(f"[DEBUG] signal={signal}, price={price}, stop_distance={stop_distance}")

            if signal in ("BUY", "SELL"):
                now = time.time()
                if now - last_signal_time < MIN_TIME_BETWEEN_TRADES:
                    log.debug("Skipping due to trade spacing limit")
                else:
                    trade_res = open_trade(price, stop_distance, side=signal)
                    if trade_res.get("success"):
                        last_signal_time = now
                    else:
                        log.debug(f"trade skipped/fail: {trade_res.get('reason') or trade_res.get('result')}")
            else:
                log.info("No signal — waiting...")

            balance = safe_get_account_balance()
            dashboard_data["account_balance"] = balance
            update_balance_tracking(balance)
            dashboard_data["heartbeat"] = "Online ✅"
            log.info("Bot heartbeat ✅")
            elapsed = time.time() - t0
            to_sleep = max(0.01, LOOP_SLEEP - elapsed)
            time.sleep(to_sleep)

        except Exception as e:
            log.error(f"main loop exception: {e}")
            traceback.print_exc()
            dashboard_data["heartbeat"] = f"Error: {e}"
            time.sleep(1)

# --------------------------
# Flask dashboard & routes
# --------------------------
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Nija Trading Bot Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; background:#0b0b0b; color:#eee; padding:18px; }
    h1 { color:#4ee08a; margin-bottom:6px; }
    .card { background:#111; padding:14px; margin:8px 0; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.6); }
    .muted { color:#9aa; font-size:0.9em; }
  </style>
  <meta http-equiv="refresh" content="2">
</head>
<body>
  <h1>Nija Trading Bot</h1>
  <div class="card"><strong>Status:</strong> {{ heartbeat }} <span class="muted">({{ status_notes }})</span></div>
  <div class="card"><strong>Account Balance:</strong> ${{ account_balance }}</div>
  <div class="card"><strong>Last Signal:</strong> {{ last_signal }}</div>
  <div class="card"><strong>Last Trade:</strong> {{ last_trade }}</div>
  <div class="card"><strong>Trailing Stop Loss:</strong> ${{ trailing_stop }}</div>
  <div class="card"><strong>Trailing Take Profit:</strong> ${{ trailing_take_profit }}</div>
  <div class="card muted">Refreshes every 2s. Heartbeat endpoint: <code>/heartbeat</code></div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML, **dashboard_data)

@app.route("/heartbeat")
def heartbeat():
    return jsonify({"status": "alive", "heartbeat": dashboard_data.get("heartbeat"), "notes": dashboard_data.get("status_notes")})

@app.route("/stats")
def stats():
    now = int(time.time())
    counts = {"1m":0, "5m":0, "15m":0}
    cutoff_1 = now - 60
    cutoff_5 = now - 300
    cutoff_15 = now - 900
    ts_list = list(_trade_timestamps)
    for t in ts_list:
        if t >= cutoff_1: counts["1m"] += 1
        if t >= cutoff_5: counts["5m"] += 1
        if t >= cutoff_15: counts["15m"] += 1
    recent = [datetime.fromtimestamp(t, tz=timezone.utc).isoformat() for t in ts_list[-10:]]
    return jsonify({
        "total_trades": _total_trades,
        "trades_last_1m": counts["1m"],
        "trades_last_5m": counts["5m"],
        "trades_last_15m": counts["15m"],
        "recent_trades": recent,
        "last_trade": dashboard_data.get("last_trade"),
        "heartbeat": dashboard_data.get("heartbeat")
    })

# --------------------------
# Run: start background loop + Flask
# --------------------------
if __name__ == "__main__":
    # Start the trading loop in background thread so Flask remains responsive.
    threading.Thread(target=live_trading_loop, daemon=True).start()
    # Start Flask web server (keeps Replit process alive)
    app.run(host="0.0.0.0", port=8080)
