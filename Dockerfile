# Use official Python runtime
FROM python:3.11-slim

# Unbuffered output and no .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS packages required for pip builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first for caching
COPY requirements.txt .

# Upgrade pip & install Python packages
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

EXPOSE 10000

CMD ["bash", "start.sh"]
