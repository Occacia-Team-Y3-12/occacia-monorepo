import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.core.database import Base, engine
from app.core.exceptions import add_exception_handlers
from app.routers import api_router
from app.scripts.seed import seed_data


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("SKIP_DB_STARTUP") == "1":
        logger.info("SKIP_DB_STARTUP=1 set. Skipping DB startup checks and seeding.")
        yield
        return

    from app.models import registry  # noqa: F401

    logger.info("Starting up... waiting for database...")
    db_connected = False
    for i in range(15):
        try:
            Base.metadata.create_all(bind=engine)
            db_connected = True
            logger.info("Database connection successful.")
            break
        except OperationalError:
            logger.warning("Database unavailable, retrying in 2s... (%s/15)", i + 1)
            await asyncio.sleep(2)

    if not db_connected:
        logger.critical("Database failed to start after 30s. Continuing without DB.")
        yield
        return

    try:
        seed_data()
    except Exception as e:
        logger.warning("Seeding warning: %s", e)

    # ── Start background cleanup task ────────────────────────────────
    cleanup_task = asyncio.create_task(_run_cleanup_job())
    logger.info("🧹 Chat history cleanup job started.")

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def _run_cleanup_job():
    """Runs every 24 hours to delete chat messages older than 30 days."""
    from app.core.database import SessionLocal
    from app.services.chat_service import chat_service

    while True:
        await asyncio.sleep(86400)  # 24 hours
        try:
            db = SessionLocal()
            chat_service.cleanup_old_sessions(db, days=30)
            db.close()
        except Exception as e:
            logger.error(f"🧹 Cleanup job error: {e}")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Occacia Event Backend",
        description="Occacia backend APIs",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",           # nginx in Docker
        "http://localhost:80",
        "http://localhost:3000",      # Next.js local dev (npm run dev)
        "http://127.0.0.1:3000",
        "http://localhost:8000",      # direct backend access
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    add_exception_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()
# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth_router,
    vendor_router,
    package_router,
    order_router,
    review_router,
    health_router,
    admin_router  # Add this
)

app = FastAPI(
    title="Occacia API",
    description="AI-powered occasion planning platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/v1")
app.include_router(vendor_router.router, prefix="/api/v1")
app.include_router(package_router.router, prefix="/api/v1")
app.include_router(order_router.router, prefix="/api/v1")
app.include_router(review_router.router, prefix="/api/v1")
app.include_router(admin_router.router, prefix="/api/v1")  # Add this
app.include_router(health_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Occacia API"}