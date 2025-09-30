from flask import request
import json, os
import re

def normalize_symbol_for_exchange(raw_symbol, markets):
    """
    Try to convert many possible incoming symbol formats into an exchange-usable symbol.
    Strategies (in order):
      - If raw_symbol already in markets -> return it
      - Replace separators (space, -, :, /) with '/'
      - Try uppercase, try dash '-'
      - Try inserting '/' between base and quote using common quote list
      - Fallback: find first market whose base+quote matches raw (very permissive)
    """
    if not raw_symbol:
        return None

    s = raw_symbol.strip()
    # if someone already sent as JSON symbol like "BTC/USD"
    if s in markets:
        return s

    # canonicalize separators
    s2 = re.sub(r'[\s\-\_:]+', '/', s).upper()  # e.g. DOGEUSD -> DOGE/USD, DOGE_USD -> DOGE/USD

    if s2 in markets:
        return s2

    # try dash form
    s_dash = s2.replace('/', '-')
    if s_dash in markets:
        return s_dash

    # try removing slash (some markets are like BTCUSD)
    s_noslash = s2.replace('/', '')
    for key in markets.keys():
        if key.replace('/', '').upper() == s_noslash:
            return key

    # try to split into base/quote by checking known quotes
    common_quotes = ['USD','USDT','BTC','ETH','EUR','GBP','USD:USD']
    for q in common_quotes:
        if s2.endswith(q):
            base = s2[:-len(q)]
            cand = f"{base}/{q}"
            if cand in markets:
                return cand
            cand2 = f"{base}-{q}"
            if cand2 in markets:
                return cand2

    # last resort: fuzzy match — look for market whose base+quote equals raw ignoring separators
    raw_compact = re.sub(r'[^A-Z0-9]', '', s2)
    for key in markets.keys():
        if re.sub(r'[^A-Z0-9]', '', key.upper()) == raw_compact:
            return key

    # couldn't find normalized symbol
    return None

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.data.decode("utf-8", errors="replace")
    print("---- WEBHOOK RECEIVED ----")
    print("Headers:", dict(request.headers))
    print("Raw body:", raw_body[:2000])

    alert = None

    # 1) Direct whole-body JSON
    try:
        alert = json.loads(raw_body)
        print("✅ Parsed whole-body JSON:", alert)
    except Exception:
        # 2) try to extract first JSON object inside body (naive brace-matching)
        start = raw_body.find('{')
        if start != -1:
            depth = 0
            end = -1
            for i, ch in enumerate(raw_body[start:], start):
                if ch == '{': depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end != -1:
                candidate = raw_body[start:end+1]
                try:
                    alert = json.loads(candidate)
                    print("✅ Extracted JSON object:", alert)
                except Exception:
                    print("⚠️ Extracted JSON failed to parse. Candidate:", candidate[:500])
            else:
                print("⚠️ Found '{' but no matching '}'")
        else:
            print("⚠️ No JSON found in body")

    # 3) fallback to plain text
    if alert is None:
        alert = {"raw_text": raw_body}
        print("ℹ️ Falling back to plain-text handling.")

    # Standardize keys if someone sent 'market' or 'type'
    market_field = (alert.get("market") or alert.get("type") or "spot").lower()

    # Accept multiple naming variants for symbol/side/amount
    symbol = alert.get("symbol") or alert.get("ticker") or alert.get("pair") or None
    side = (alert.get("side") or alert.get("action") or "").lower()
    amount = alert.get("amount") or alert.get("qty") or alert.get("quantity") or alert.get("size") or None

    # If the alert is plain text, attempt to parse common patterns like "order buy @ 2 filled on DOGEUSD"
    if symbol is None and "raw_text" in alert:
        txt = alert["raw_text"]
        # try to find a token that looks like a pair: e.g. DOGEUSD or DOGE/USD
        m = re.search(r'([A-Za-z]{2,5}[-_/:]?[A-Za-z0-9]{2,6})', txt)
        if m:
            symbol = m.group(1)
        # find buy/sell
        if not side:
            if re.search(r'\bbuy\b', txt, re.I): side = "buy"
            elif re.search(r'\bsell\b', txt, re.I): side = "sell"
        # find simple numeric amount
        if not amount:
            m2 = re.search(r'@?\s*([0-9]+(?:\.[0-9]+)?)', txt)
            if m2:
                amount = m2.group(1)

    # Validate and normalize symbol to an exchange-accepted market
    normalized = None
    try:
        markets = SPOT_CLIENT.load_markets() if market_field == "spot" else FUTURES_CLIENT.load_markets()
    except Exception:
        # if load_markets fails, still allow simulated behavior
        markets = {}

    if symbol:
        normalized = normalize_symbol_for_exchange(symbol, markets)
        if not normalized:
            # try some common alternative formats
            cand_try = symbol.replace('-', '/').replace('_', '/')
            normalized = normalize_symbol_for_exchange(cand_try, markets)

    # Convert amount to float if present
    try:
        if amount is not None:
            amount = float(amount)
    except Exception:
        print("⚠️ amount conversion failed:", amount)
        amount = None

    # Decide whether to execute or dry-run
    DRY_RUN = os.getenv("DRY_RUN", "").lower() in ("1","true","yes")
    can_place = (side in ("buy","sell")) and normalized and (amount and amount > 0)

    if can_place:
        client = SPOT_CLIENT if market_field == "spot" else FUTURES_CLIENT
        if DRY_RUN:
            print(f"🟡 DRY-RUN: Would place {side.upper()} order for {amount} {normalized} on {market_field.upper()}")
        else:
            try:
                print(f"🔔 Placing LIVE {side.upper()} order for {amount} {normalized} on {market_field.upper()}")
                order = client.create_order(normalized, 'market', side, amount)
                print("✅ Order placed:", order)
            except Exception as e:
                print("❌ Order failed:", type(e).__name__, str(e))
    else:
        print("⚠️ Ignored webhook — missing/invalid fields or symbol normalization failed.")
        print("Parsed:", {"symbol": symbol, "normalized": normalized, "side": side, "amount": amount, "market": market_field})

    return "OK", 200
