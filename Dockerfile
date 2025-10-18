# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

# Ensure pip & wheel are up to date, then install requirements
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Make start script executable (we'll add start.sh below)
RUN chmod +x /app/start.sh || true

# Expose the port your Flask app uses (10000 per your logs)
EXPOSE 10000

# Default command
CMD ["bash", "start.sh"]
