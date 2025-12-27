FROM python:3.11-slim

# 1. THE SYSTEM ARMOR: Install 'libpq-dev' and 'gcc'
# These are required to compile the 'psycopg2' driver for Postgres
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. CACHE LAYER: Install dependencies first to speed up future builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. PAYLOAD: Copy the rest of the backend code
COPY . .

# 4. THE IGNITION KEY: Prepare the start script
# We use 'chmod' to make sure Linux has permission to run our script
RUN chmod +x start.sh

# 5. EXECUTION: Instead of running Python directly, we run the Orchestrator
# This script runs: alembic upgrade head && uvicorn main:app
CMD ["./start.sh"]