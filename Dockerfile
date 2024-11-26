FROM python:3.9-slim

# Dependency fix
RUN apt-get update && apt-get install -y \
    libselinux1 \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install flask gunicorn

EXPOSE 5000

ENV FLASK_ENV=production

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
