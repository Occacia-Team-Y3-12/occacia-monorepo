# 1. Base Image: Lightweight Python 3.11
FROM python:3.11-slim

# 2. Set Environment Variables (Prevents Python buffering & creating .pyc files)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Create and set working directory
WORKDIR /app

# 4. Install System Dependencies (Crucial for Postgres & Fuzzy Logic)
# We need gcc and libpq-dev to compile the C-extensions for python-Levenshtein
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy Dependencies first (Docker Cache Layering Strategy)
COPY requirements.txt .

# 6. Install Python Libraries
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the application code
COPY . .

# 8. Expose the port
EXPOSE 8000

# 9. Command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]