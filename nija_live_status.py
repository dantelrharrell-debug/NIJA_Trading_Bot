import json, os, requests

# ---------- CONFIG ----------
DASH_FILE = "data/dashboard.json"  # same as Nija Trading Bot dashboard

# --- Webhook auto-read and trim ---
TRADINGVIEW_WEBHOOK = os.getenv("TRADINGVIEW_WEBHOOK","https://nija-trading-bot.onrender.com/webhook").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN","").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID","").strip()

# ---------- FUNCTIONS ----------
def load_dashboard():
    try:
        data = json.load(open(DASH_FILE,"r"))
        return data
    except:
        return {}

def check_tradingview_webhook():
    if TRADINGVIEW_WEBHOOK:
        try:
            r = requests.post(TRADINGVIEW_WEBHOOK, json={"test":"ping"}, timeout=2)
            return "✅ Live" if r.status_code==200 else f"⚠️ HTTP {r.status_code}"
        except:
            return "❌ Not reachable"
    return "⚠️ Not set"

def check_telegram():
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=2)
            return "✅ Connected" if r.status_code==200 else f"⚠️ HTTP {r.status_code}"
        except:
            return "❌ Not reachable"
    return "⚠️ Not set"

# ---------- MAIN ----------
dashboard = load_dashboard()
print("\n📊 Nija Trading Bot Live Status")
print("-"*50)
if dashboard:
    for asset, info in dashboard.items():
        print(f"{asset}: Profit ${info['profit']:.2f} | Leverage {info['leverage']}x | Trades {info['trades']}")
else:
    print("⚠️ No dashboard data yet. Bot may not have traded.")

print("-"*50)
print(f"TradingView Webhook: {check_tradingview_webhook()}")
print(f"Telegram Alerts: {check_telegram()}")
