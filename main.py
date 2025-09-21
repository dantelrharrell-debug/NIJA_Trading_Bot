# main.py
from flask import Flask, request, jsonify
import os

# ===============================
# CREATE THE FLASK APP FIRST
# ===============================
app = Flask(__name__)

# ===============================
# HEALTH CHECK ROUTE
# ===============================
@app.route("/health", methods=["GET"])
def health():
    """
    Simple health endpoint to check if the app is running.
    """
    return jsonify({
        "status": "ok",
        "live": os.getenv("NIJA_LIVE", "false")
    }), 200

# ===============================
# WEBHOOK ROUTE
# ===============================
@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receives TradingView or other webhook POST requests.
    Validates the token and prints data to logs.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    token = data.get("token") if isinstance(data, dict) else None
    if not token:
        token = request.headers.get("X-Webhook-Token")

    if token != os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken"):
        return jsonify({"error": "unauthorized"}), 401

    # Log the received webhook to Render logs
    print("Webhook received:", data)

    # Return the received payload for confirmation
    return jsonify({"received": data, "message": "webhook accepted"}), 200

# ===============================
# RUN THE APP
# ===============================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # debug=True prints errors to the console if anything fails
    app.run(host="0.0.0.0", port=port, debug=True)
