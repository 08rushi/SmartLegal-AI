# SmartLegal AI backend image (host-agnostic: Render, Railway, Fly, VPS, ...).
# Build from the backend/ directory:  docker build -t smartlegal-api backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Tesseract (+ Hindi/Marathi/English data) for scanned documents, curl for health checks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

# Applies pending Alembic migrations, then starts the API. Production never creates tables
# itself (AUTO_CREATE_SCHEMA=false), so a failed migration stops the container clearly.
# --proxy-headers lets rate limits see the real client IP behind the platform proxy;
# keep FORWARDED_ALLOW_IPS limited to your proxy's address when you know it.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-*}"]
