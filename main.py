# main.py

# ✅ Correct imports
import os
from coinbase_advanced_py import CoinbaseAdvanced  # correct module name
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------
# API Credentials
# -----------------------------
API_KEY = os.getenv("API_KEY") or "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = os.getenv("API_SECRET") or "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

# -----------------------------
# Risk Settings (AI adjustable)
# -----------------------------
MIN_RISK_PERCENT = 2    # minimum 2% per trade
MAX_RISK_PERCENT = 10   # maximum 10% per trade

# -----------------------------
# Initialize Coinbase Advanced client
# -----------------------------
cb = CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)

# -----------------------------
# Example: Check account balances
# -----------------------------
def show_balances():
    try:
        accounts = cb.get_accounts()
        for account in accounts:
            print(f"{account['currency']}: {account['balance']}")
    except Exception as e:
        print("Error fetching balances:", e)

# -----------------------------
# AI Trade logic (simplified placeholder)
# -----------------------------
def trade_logic():
    # Example: dynamically adjust risk per trade between 2% and 10%
    current_risk = MIN_RISK_PERCENT  # your AI can overwrite this
    print(f"Trading with risk: {current_risk}%")
    # Placeholder: add your AI trading strategy here
    # cb.place_order(symbol="BTC-USD", side="buy", size=..., price=..., risk=current_risk)
    pass

# -----------------------------
# Main execution
# -----------------------------
if __name__ == "__main__":
    show_balances()
    trade_logic()
    print("Nija Trading Bot is live ✅")
