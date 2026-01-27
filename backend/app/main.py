import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.database import engine, Base

# --- IMPORT ROUTERS ---
from app.routers import auth
from app.routers import planning

# --- IMPORT SEEDER ---
from app.seed import seed_data 

# 🛠️ APP INITIALIZATION
# root_path="/api" fixes the Swagger UI behind Nginx
app = FastAPI(
    title="Occacia Event Backend",
    root_path="/api" 
)

# CORS (Allow Frontend to talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTERS ---
app.include_router(auth.router)
app.include_router(planning.router)

# =========================================================
# 🛡️ STARTUP LOGIC: WAIT FOR DB & SEED DATA
# =========================================================
@app.on_event("startup")
def startup_event():
    print("⏳ Starting up... Waiting for Database to wake up...")
    
    # 1. RETRY LOOP: Wait for Postgres (Fixes "Race Condition" on new PCs)
    db_connected = False
    for i in range(15): # Try 15 times (30 seconds total)
        try:
            # Try to create tables. If DB is locked/starting, this will fail safely.
            Base.metadata.create_all(bind=engine)
            db_connected = True
            print("✅ Database connection successful!")
            break
        except OperationalError:
            print(f"⚠️ Database unavailable, retrying in 2s... ({i+1}/15)")
            time.sleep(2)
            
    if not db_connected:
        print("❌ CRITICAL: Database failed to start after 30s. Exiting.")
        return

    # 2. RUN SEEDER (Only runs if DB is empty)
    # Now safe because we know the connection is solid.
    print("🌱 Checking Seed Data...")
    try:
        seed_data()
    except Exception as e:
        print(f"⚠️ Seeding warning: {e}")

@app.get("/health")
def health_check():
    return {"status": "active", "system": "Occacia Core"}