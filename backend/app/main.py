from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- SECURITY IMPORT
from . import models
from .database import engine
from .routers import vendors

# ---------------------------------------------------------
# 1. DATABASE INIT (The Construction Crew)
# ---------------------------------------------------------
# This checks if tables exist. If not, it builds them.
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# 2. APP DEFINITION
# ---------------------------------------------------------
app = FastAPI(title="Occacia API", version="1.0.0")

# ---------------------------------------------------------
# 3. SECURITY (CORS) - The "Guest List"
# ---------------------------------------------------------
# This allows your Frontend to talk to this Backend.
origins = [
    "http://localhost:3000",  # React Default
    "http://localhost:5173",  # Vite/Next.js Default
    "http://127.0.0.1:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Who is allowed to enter?
    allow_credentials=True,     # Allow cookies/auth headers?
    allow_methods=["*"],        # Allow all types (GET, POST, PUT, DELETE)
    allow_headers=["*"],        # Allow all headers
)

# ---------------------------------------------------------
# 4. ROUTERS (The Departments)
# ---------------------------------------------------------
app.include_router(vendors.router)

# ---------------------------------------------------------
# 5. HEALTH CHECK (The Heartbeat)
# ---------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "status": "active",
        "system": "Occacia API",
        "database": "connected"
    }