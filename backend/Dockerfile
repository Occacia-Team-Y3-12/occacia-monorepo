# Build dependencies once and copy the virtualenv into a smaller runtime image.
FROM ghcr.io/library/python:3.11-slim AS builder

RUN apt-get update && apt-get upgrade -y --no-install-recommends && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep Poetry-managed dependencies inside the project so the venv can be copied as a unit.
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

RUN pip install --no-cache-dir poetry==2.3.2

# Install only runtime app dependencies into /app/.venv.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-ansi && \
    find /app/.venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Runtime image for OCI/container deployment.
FROM ghcr.io/library/python:3.11-slim

# Use the copied virtualenv directly and keep container logs unbuffered.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install only OS packages needed at runtime by psycopg2 and the healthcheck.
RUN apt-get update && apt-get upgrade -y --no-install-recommends && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel --no-cache-dir

# Copy the prebuilt Python environment first, then the application source.
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Make the startup script executable and drop root privileges for the running app.
RUN chmod +x /app/start.sh && useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Healthcheck mirrors the FastAPI health endpoint used by compose/orchestration.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# start.sh runs Alembic migrations first, then launches Uvicorn.
CMD ["./start.sh"]
