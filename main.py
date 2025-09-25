import os
from flask import Flask, jsonify
from nija import NijaBot  # Make sure nija.py is in the same folder

app = Flask(__name__)

# Initialize the bot with full live settings
bot = NijaBot(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    live=True,              
    tp_percent=0.5,         
    sl_percent=0.3,         
    trailing_stop=True,     
    trailing_tp=True,       
    smart_logic=True        
)

@app.route("/")
def root():
    return "Nija Trading Bot is live ✅", 200

@app.route("/health")
def health():
    status = bot.check_status()
    return jsonify({"status": "live" if status else "offline"})

if __name__ == "__main__":
    import os, threading, time
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Using PORT={port}")
    try:
        threading.Thread(target=bot.run_bot, daemon=True).start()
        print("[startup] Bot thread started")
    except Exception as e:
        print("[startup] bot thread failed:", e)
    time.sleep(1)
    app.run(host="0.0.0.0", port=port)
