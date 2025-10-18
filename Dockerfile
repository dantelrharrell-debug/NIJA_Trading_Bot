# Use official Python runtime
FROM python:3.11-slim

# Keep output unbuffered & avoid .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS deps needed to build some Python packages (adjust if you know what's required)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl gcc libssl-dev libffi-dev \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements early to leverage cache
COPY requirements.txt /app/

# Upgrade pip & install Python deps
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Make start script executable
RUN chmod +x /app/start.sh || true

# Expose the port your Flask app uses (10000 per your logs)
EXPOSE 10000

# Use the start script as entrypoint
CMD ["bash", "start.sh"]
