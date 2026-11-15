# SmartLegal AI - single container: builds the React frontend and serves it together with the API.
# Build from the repo root:  docker build -t smartlegal .
# One origin => first-party login cookie, no CORS, works on a free host without a custom domain.

# ---- 1) build the frontend --------------------------------------------------------------------
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# "/" = call the API on the same origin (see frontend/src/services/api.ts)
ENV VITE_API_BASE_URL=/
RUN npm run build

# ---- 2) API + static site ---------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Tesseract (+ Hindi/Marathi/English data) for scanned documents, curl for the health check.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
COPY --from=web /web/dist ./static

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

# Applies pending Alembic migrations, then starts the API (which also serves ./static).
# Production never creates tables itself (AUTO_CREATE_SCHEMA=false), so a failed migration stops
# the container with a clear error. --proxy-headers gives rate limits the real client IP.
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-*}"]
