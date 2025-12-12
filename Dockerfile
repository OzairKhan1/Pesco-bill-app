# ---- Build Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system packages required for building Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (Flask + Werkzeug only)
COPY requirements.txt .

# Install all dependencies into a separate folder
RUN pip install --prefix=/install -r requirements.txt

# Copy entire source code
COPY . .

# ---- Runtime Stage ----
FROM python:3.11-slim AS runner

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy runtime files (only those that exist)
COPY --from=builder /app/app.py ./app.py
COPY --from=builder /app/templates ./templates
COPY --from=builder /app/uploads ./uploads
COPY --from=builder /app/extract_images.py ./extract_images.py

# Expose Flask port
EXPOSE 5000

# Environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start Flask app
CMD ["python", "app.py"]

