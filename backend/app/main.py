import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.core.database import engine, Base

# --- IMPORT MODELS ---
# ✅ CRITICAL: You must import your models here so Base knows they exist 
# before calling create_all()
from app.models import chat_model 

# --- IMPORT ROUTERS ---
from app.routers import auth
from app.routers import planning

# --- IMPORT EXCEPTION HANDLERS ---
from app.core.exceptions import add_exception_handlers

# --- IMPORT SEEDER ---
from app.scripts.seed import seed_data 

# =========================================================
# 📝 LOGGING CONFIGURATION
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
    root_path="/api"  # Essential for Nginx Reverse Proxy
)

# CORS: Allows your Frontend (React/Next.js) to communicate with this API
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

# 1. Apply Global Exception Handlers
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
    
    # 1. RETRY LOOP: Wait for Postgres (Fixes Docker "Race Condition")
    db_connected = False
    for i in range(15): 
        try:
            # ✅ create_all now sees 'chat_history' because we imported chat_model
            Base.metadata.create_all(bind=engine)
            db_connected = True
            logger.info("✅ Database connection successful and Tables synchronized!")
            break
        except OperationalError:
            logger.warning(f"⚠️ Database unavailable, retrying in 2s... ({i+1}/15)")
            time.sleep(2)
            
    if not db_connected:
        logger.critical("❌ CRITICAL: Database failed to start. System halting.")
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
    return {"status": "active", "system": "Occacia Core"}