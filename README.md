# 🥷 NIJA Trading Bot

The **Nija Trading Bot** is a self-healing, Coinbase Advanced API trading bot built with Python and `coinbase_advanced_py`.  
It is designed to run as a **Render Background Worker** — no open ports, no web server, just clean trading automation.  

---

## ⚙️ Features

- ✅ Uses official **Coinbase Advanced API**
- ✅ Designed for **Render Background Worker**
- ✅ Self-heals and logs errors automatically
- ✅ Optional **LIVE_TRADING** mode
- ✅ Fetches BTC/USD prices and can run custom strategies

---

## 🚀 Setup Instructions

1. **Environment Variables (on Render):**
   - `API_KEY` → Your Coinbase API key  
   - `API_SECRET` → Your Coinbase API secret  
   - `LIVE_TRADING` → `False` (for testing) or `True` (for live trading)

2. **Deploy as a Background Worker:**
   - Go to your Render Dashboard →  
     **New + → Worker → Connect to your repo**
   - Set your Start Command to:
     ```
     .venv/bin/python3 nija_bot.py
     ```

3. **Confirm your requirements file:**
   Make sure `requirements.txt` contains:
