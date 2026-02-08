# 1. Base Image: Lightweight Python 3.14
FROM python:3.14-slim

# 2. Set Environment Variables (Prevents Python buffering & creating .pyc files)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false

# 3. Create and set working directory
WORKDIR /app

# 4. Upgrade packaging tooling and install Poetry
RUN python -m pip install --no-cache-dir -U pip setuptools wheel \
    && python -m pip install --no-cache-dir "poetry==2.3.2"

# 5. Copy application code (includes `poetry.lock` if committed)
COPY . .

# 6. Install Python Libraries (main only)
RUN poetry install --only main --no-root

# 7. Expose the port
EXPOSE 8000

# 8. Command to run the app
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
