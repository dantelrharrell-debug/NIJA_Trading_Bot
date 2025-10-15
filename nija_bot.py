#!/usr/bin/env python3
# nija_bot.py — robust Coinbase client autodetector + safe fallback

import os
import importlib
import inspect
import traceback
from flask import Flask, jsonify

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

def debug(msg):
    print("DEBUG:", msg)

# ----------------------
# MockClient fallback
# ----------------------
class MockClient:
    def get_account_balances(self):
        return {'USD': 10000.0, 'BTC': 0.05}
    def place_order(self, *a, **k):
        raise RuntimeError("DRY RUN: MockClient refuses to place orders")

# ----------------------
# Coinbase detection + client init
# ----------------------
def find_coinbase_module():
    try:
        m = importlib.import_module("coinbase")
        debug(f"imported module -> {m.__name__}")
        return m
    except Exception as e:
        debug(f"failed to import 'coinbase': {e}")
        return None

def collect_candidates(cb_mod):
    candidates = []
    for sub in ("rest", "websocket", "api_base", "client"):
        try:
            sm = importlib.import_module(f"coinbase.{sub}")
            debug(f"found submodule coinbase.{sub}")
            for name, obj in inspect.getmembers(sm, lambda o: inspect.isclass(o) or inspect.isfunction(o)):
                lowered = name.lower()
                if any(k in lowered for k in ("client", "rest", "api", "ws", "websocket")):
                    candidates.append((f"coinbase.{sub}.{name}", obj))
        except Exception:
            pass
    try:
        for name, obj in inspect.getmembers(cb_mod, lambda o: inspect.isclass(o) or inspect.isfunction(o)):
            lowered = name.lower()
            if any(k in lowered for k in ("client", "rest", "api")):
                candidates.append((f"coinbase.{name}", obj))
    except Exception:
        pass
    # dedupe
    seen = {}
    for fullname, obj in candidates:
        if fullname not in seen:
            seen[fullname] = obj
    return list(seen.items())

def try_instantiate(candidate_obj, api_key, api_secret):
    if inspect.isfunction(candidate_obj):
        for args in [(api_key, api_secret), ()]:
            try:
                debug(f"trying function {candidate_obj.__name__} with args {args}")
                return candidate_obj(*args)
            except Exception as e:
                debug(f"function call failed: {type(e).__name__} {e}")
    if inspect.isclass(candidate_obj):
        attempts = [
            ((api_key, api_secret), {}),
            ((), {"api_key": api_key, "api_secret": api_secret}),
            ((), {"key": api_key, "secret": api_secret}),
            ((), {"client_id": api_key, "client_secret": api_secret}),
        ]
        for args, kwargs in attempts:
            try:
                debug(f"trying class {candidate_obj.__name__} with args={args} kwargs={list(kwargs.keys())}")
                return candidate_obj(*args, **kwargs)
            except Exception as e:
                debug(f"construction failed: {type(e).__name__} {e}")
    raise RuntimeError("All instantiation attempts failed for candidate.")

cb = find_coinbase_module()
if cb and API_KEY and API_SECRET:
    candidates = collect_candidates(cb)
    debug(f"candidates found ({len(candidates)}): {[name for name, _ in candidates]}")
    for fullname, obj in candidates:
        try:
            inst = try_instantiate(obj, API_KEY, API_SECRET)
            if inst and (hasattr(inst, "get_account_balances") or hasattr(inst, "get_accounts") or hasattr(inst, "list_accounts")):
                client = inst
                LIVE_TRADING = True
                debug(f"SUCCESS: instantiated client from {fullname}. LIVE_TRADING=True")
                break
        except Exception as e:
            debug(f"candidate {fullname} failed: {type(e).__name__} {e}")
            debug(traceback.format_exc())

if not LIVE_TRADING or client is None:
    debug("WARN: falling back to MockClient (no live Coinbase client available)")
    client = MockClient()

# ----------------------
# Startup balances (safe)
# ----------------------
try:
    balances = client.get_account_balances()
except Exception as e:
    debug(f"Error reading balances: {type(e).__name__} {e}")
    balances = {"error": str(e)}

print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ----------------------
# Flask setup
# ----------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

# ----------------------
# Start Flask server
# ----------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
