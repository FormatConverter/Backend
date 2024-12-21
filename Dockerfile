# # ------------------------------
# # Stage 1: Build Whisper.cpp
# # ------------------------------
FROM python:3.9-slim AS whisperbuild
RUN apt-get update && \
    apt-get install -y curl gcc g++ make cmake libglib2.0-0 libsm6 libxext6 libxrender-dev ffmpeg git

WORKDIR /whisper.cpp
RUN git clone https://github.com/ggerganov/whisper.cpp . && \
    cmake -B build && \
    make -C build
RUN bash ./models/download-ggml-model.sh base.en
RUN bash ./models/download-ggml-model.sh tiny.en


# # ------------------------------
# # Stage 2: Base Stage
# # ------------------------------

FROM whisperbuild AS base

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libselinux1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------------------------------
# Stage 3: Build Stage
# ------------------------------
FROM base AS build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Stage 4: Production
# ------------------------------
FROM base AS production

# Copy Whisper.cpp binaries from whisperbuild stage
COPY --from=whisperbuild /whisper.cpp /whisper.cpp

# Copy application files
COPY --from=build /usr/local /usr/local
COPY . .

# Set environment variables for Flask
ENV FLASK_ENV=production

# Expose application port
EXPOSE 5050

# Command to run the app
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5050", "app:app", "--timeout", "600"]
