# ---------- robust RESTClient instantiation ----------
pem_temp_path = None
if API_PEM:
    try:
        import tempfile
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="wb")
        tf.write(API_PEM.encode("utf-8"))
        tf.flush()
        tf.close()
        pem_temp_path = tf.name
        print("✅ Wrote API_PEM to temporary file:", pem_temp_path)
    except Exception as e:
        print("❌ Failed to write API_PEM to temp file:", e)
        pem_temp_path = None

client = None
instantiated_with = None

# Try constructors safely — never pass api_key + key_file together
if pem_temp_path:
    # Prefer PEM-based auth if the PEM was provided
    try:
        print("ℹ️ Attempting RESTClient(key_file=pem_temp_path) ...")
        client = RESTClient(key_file=pem_temp_path)
        instantiated_with = "key_file"
        print("✅ RESTClient instantiated with key_file (PEM).")
    except Exception as e:
        print("⚠️ RESTClient(key_file=...) failed:", type(e).__name__, e)
        import traceback; traceback.print_exc()
        # fallback: try api_key/api_secret if provided (but do NOT pass both at once)
        if API_KEY and API_SECRET:
            try:
                print("ℹ️ Falling back to RESTClient(api_key, api_secret) ...")
                client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
                instantiated_with = "api_key+api_secret (fallback)"
                print("✅ RESTClient instantiated with api_key+api_secret (fallback).")
            except Exception as e2:
                print("❌ Fallback RESTClient(api_key,api_secret) also failed:", type(e2).__name__, e2)
                import traceback; traceback.print_exc()
                if not DRY_RUN:
                    raise SystemExit(1)
        else:
            if not DRY_RUN:
                raise SystemExit(1)
else:
    # No PEM provided — try API key + secret
    if API_KEY and API_SECRET:
        try:
            print("ℹ️ Attempting RESTClient(api_key=..., api_secret=...) ...")
            client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
            instantiated_with = "api_key+api_secret"
            print("✅ RESTClient instantiated with api_key+api_secret.")
        except Exception as e:
            print("❌ RESTClient(api_key,api_secret) failed:", type(e).__name__, e)
            import traceback; traceback.print_exc()
            if not DRY_RUN:
                raise SystemExit(1)
    else:
        print("⚠️ No API_PEM and no API_KEY/API_SECRET provided — cannot create REST client.")
        if not DRY_RUN:
            raise SystemExit(1)

print("ℹ️ Instantiation result:", instantiated_with, "client:", type(client) if client else None)
# ---------- end instantiation ----------
