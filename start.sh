cat > start.sh <<'SH'
#!/bin/bash
PORT_NUMBER=${PORT:-5000}
exec gunicorn main:app --bind 0.0.0.0:$PORT_NUMBER --workers 3
SH

chmod +x start.sh
