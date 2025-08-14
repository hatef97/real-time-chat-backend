FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps kept minimal (certs & tzdata are tiny and safe)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata \
  && rm -rf /var/lib/apt/lists/*

# Install deps first to leverage Docker layer cache
COPY requirements.txt /app/requirements.txt
# Prefer binary wheels to avoid compiling from source
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# App code
COPY . /app

# Optional: run entrypoint (handles migrate, etc.)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/bin/sh","/app/entrypoint.sh"]