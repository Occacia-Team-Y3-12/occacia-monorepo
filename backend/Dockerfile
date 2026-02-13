# ==========================================
# STAGE 1: The Builder (The Workshop)
# ==========================================
FROM python:3.12-slim AS builder

# 1. Install system build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Configure Poetry via Environment Variables (Bulletproof method)
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR='/tmp/poetry_cache'

RUN pip install --no-cache-dir poetry==2.0.1

# 3. Copy only the blueprint
COPY pyproject.toml ./

# 4. Generate the lock file and install into /app/.venv
# We run these together to ensure the venv is created in the right spot
RUN poetry lock && \
    poetry install --only main --no-root --no-ansi && \
    rm -rf $POETRY_CACHE_DIR

# ==========================================
# STAGE 2: The Runtime (The Vault)
# ==========================================
FROM python:3.12-slim

# Systems Optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install runtime database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 5. Teleport the FINISHED environment and code
# This will now find /app/.venv because of the config above
COPY --from=builder /app/.venv /app/.venv
COPY . .

# 6. Security: Run as a non-privileged user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Execute directly from the teleported virtualenv
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]