from flask import request, jsonify

@app.route("/webhook", methods=["POST"])
def webhook():
    # parse JSON safely
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error":"invalid json"}), 400

    # token can be in body or header
    token = data.get("token") if isinstance(data, dict) else None
    if not token:
        token = request.headers.get("X-Webhook-Token")

    if token != os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken"):
        return jsonify({"error":"unauthorized", "received_token": token}), 401

    # log to Render logs
    print("Webhook received:", data)

    # respond with 200 OK and the received payload
    return jsonify({"received": data, "message": "webhook accepted"}), 200
