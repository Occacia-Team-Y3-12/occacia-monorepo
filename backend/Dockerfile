# --- Builder Stage ---
# Compiles dependencies and builds the virtual environment
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Force Poetry to create the virtual environment directly inside the project folder
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

RUN pip install --no-cache-dir poetry==2.3.2

# Install only production dependencies and wipe the pycache to save space
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-ansi && \
    find /app/.venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# --- Runtime Stage ---
# The lightweight, production-ready container that actually runs your code
FROM python:3.11-slim

# Prevent Python from writing .pyc files and force standard output for clean Docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install only the minimal runtime libraries required for PostgreSQL and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip setuptools wheel --no-cache-dir

# Grab the pre-compiled virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Secure the container by switching from root to a restricted user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]