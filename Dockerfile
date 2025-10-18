# Base image with Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . /app

# Upgrade pip, setuptools, wheel
RUN python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Make start script executable
RUN chmod +x start.sh

# Expose port for TradingView webhook
EXPOSE 10000

# Start NIJA bot
CMD ["./start.sh"]
