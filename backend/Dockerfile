FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Use 'python' for a script or 'uvicorn' for FastAPI/Flask
CMD ["python", "main.py"]