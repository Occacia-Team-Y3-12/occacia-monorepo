import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.database import engine
from app.core.exceptions import add_exception_handlers
from app.routers import api_router
from app.scripts.seed import seed_data

# Configure logging
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
    
    # Verify database connection (schema is managed externally by Alembic)
    for i in range(15):
        try:
            with engine.connect() as conn:
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

    # Seed initial data if necessary
    try:
        seed_data()
    except Exception as e:
        logger.warning("Seeding warning: %s", e)

    # Start background tasks
    cleanup_task = asyncio.create_task(_run_cleanup_job())
    logger.info("Chat history cleanup job started.")

    yield

    # Shutdown sequence
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
            logger.error("Cleanup job error: %s", e)

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
    
    # Configure CORS for local development and production environments
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:80",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "https://app.occacia.com",
            "https://www.app.occacia.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    add_exception_handlers(application)
    application.include_router(api_router)
    return application

app = create_app()