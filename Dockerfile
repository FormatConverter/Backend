# ------------------------------
# Stage 1: Base Stage
# ------------------------------
FROM python:3.9-slim AS base

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libselinux1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------------------------------
# Stage 2: Build Stage
# ------------------------------
FROM base AS build

# Install required system dependencies, including build tools and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libselinux1 \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only the requirements file to leverage Docker's cache
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Stage 3: Production
# ------------------------------
FROM base AS production

# Copy installed dependencies from the build stage
COPY --from=build /usr/local /usr/local

# Copy application files
COPY . .

# Expose application port
EXPOSE 5050

# Set environment variable for Flask to run in production mode
ENV FLASK_ENV=production

# Command to run the app using gunicorn with 4 workers and a timeout of 600 seconds
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5050", "app:app", "--timeout", "600"]
