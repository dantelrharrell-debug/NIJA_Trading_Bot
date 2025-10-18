# Use official Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip and install dependencies
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r requirements.txt

# Make start script executable
RUN chmod +x start.sh

# Expose port for TradingView webhook
EXPOSE 10000

# Start the bot
CMD ["./start.sh"]
