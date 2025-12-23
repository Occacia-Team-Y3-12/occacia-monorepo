FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# SKEPTICAL FIX: If you use FastAPI/Flask, you MUST bind to 0.0.0.0
# Otherwise, it stays "inside" the container and you can't reach it from the IP.
CMD ["python", "main.py"]