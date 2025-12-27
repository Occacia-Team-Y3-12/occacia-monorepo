import os
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Pulls the DATABASE_URL from the docker-compose environment
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/")
def read_root():
    return {"message": "Occacia API is Online"}

@app.get("/api/db-test")
def test_db():
    try:
        # Skeptical Check: Can we actually talk to the database?
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute('SELECT version();')
        db_version = cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "Success", "db_version": db_version[0]}
    except Exception as e:
        return {"status": "Database Failed", "error": str(e)}

if __name__ == "__main__":
    # We use 0.0.0.0 so Nginx can route traffic to this Docker container
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104