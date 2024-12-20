# Use a lightweight base image
FROM python:3.9-slim

# Install only required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libselinux1 \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements file first to leverage Docker's caching layers
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files last to avoid invalidating cache on code changes
COPY . .

# Expose the application port
EXPOSE 5050

# Set environment variables
ENV FLASK_ENV=production

# Command to run the application
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5050", "app:app", "--timeout", "600"]
