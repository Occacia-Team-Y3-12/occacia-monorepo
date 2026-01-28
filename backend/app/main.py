import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.core.database import engine, Base

# --- IMPORT ROUTERS ---
from app.routers import auth
from app.routers import planning

# --- IMPORT EXCEPTION HANDLERS ---
# ✅ The Safety Net: Catches crashes and returns clean JSON
from app.core.exceptions import add_exception_handlers

# --- IMPORT SEEDER ---
# Ensure this file exists at app/core/seed.py
from app.scripts.seed import seed_data 
# =========================================================
# 📝 LOGGING CONFIGURATION (The "Eyes" of the App)
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================================================
# 🛠️ APP INITIALIZATION
# =========================================================
app = FastAPI(
    title="Occacia Event Backend",
    root_path="/api"  # Fixes Swagger UI behind Nginx
)

# CORS (Allow Frontend to talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 🔗 REGISTER COMPONENTS
# =========================================================

# 1. Apply Global Exception Handlers (The "Safety Net")
add_exception_handlers(app)

# 2. Register Routers
app.include_router(auth.router)
app.include_router(planning.router)

# =========================================================
# 🛡️ STARTUP LOGIC
# =========================================================
@app.on_event("startup")
def startup_event():
    logger.info("⏳ Starting up... Waiting for Database to wake up...")
    
    # 1. RETRY LOOP: Wait for Postgres (Fixes "Race Condition")
    db_connected = False
    for i in range(15): # Try 15 times (30 seconds total)
        try:
            # Try to create tables. If DB is locked/starting, this will fail safely.
            Base.metadata.create_all(bind=engine)
            db_connected = True
            logger.info("✅ Database connection successful!")
            break
        except OperationalError:
            logger.warning(f"⚠️ Database unavailable, retrying in 2s... ({i+1}/15)")
            time.sleep(2)
            
    if not db_connected:
        logger.critical("❌ CRITICAL: Database failed to start after 30s. Exiting.")
        return

    # 2. RUN SEEDER
    logger.info("🌱 Checking Seed Data...")
    try:
        seed_data()
        logger.info("✅ Seeding check complete.")
    except Exception as e:
        logger.error(f"⚠️ Seeding warning: {e}")

@app.get("/health")
def health_check():
    logger.info("Health check endpoint hit.")
    return {"status": "active", "system": "Occacia Core"}