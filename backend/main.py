from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Occacia API"}

@app.get("/api/status")
def get_status():
    return {"status": "Running on Oracle Tank"}

if __name__ == "__main__":
    # You MUST bind to 0.0.0.0 for Docker to see it
    uvicorn.run(app, host="0.0.0.0", port=8000)