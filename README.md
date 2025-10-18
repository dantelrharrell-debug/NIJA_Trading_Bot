# Nija Trading Bot

This is a Coinbase trading bot using `coinbase_advanced_py`.  
It is designed to run on **Render**, either as a **Background Worker** (recommended) or a **Web Service**.

## Setup

### 1. Add environment variables in Render
- `API_KEY` → Your Coinbase API key  
- `API_SECRET` → Your Coinbase secret  
- `LIVE_TRADING` → `False` or `True`  
- Optional: `API_PEM_B64` → If using PEM private key authentication  
- Optional: `NGROK_TOKEN` → If using ngrok for local tunneling  

### 2. Deployment Options

#### Background Worker (Recommended)
- No ports needed → green checks appear automatically  
- Bot automatically starts, self-heals on crashes, and logs trades  

#### Web Service (Optional)
- Must bind to a port (`PORT` environment variable required)  
- Use Flask/Gunicorn to serve a health endpoint if you want live status monitoring  
- Note: Render will show a "port scan timeout" if no port is bound  

### 3. Start the bot
- Deploy the service on Render  
- The bot will automatically initialize and run  

✅ No manual start needed for Background Worker; it restarts on failure automatically

---

## Dependencies (requirements.txt)
