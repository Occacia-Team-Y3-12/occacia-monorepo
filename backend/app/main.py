import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from app.core.database import engine
from app.core.config import settings
from app.core.exceptions import add_exception_handlers
from app.routers import api_router
from app.scripts.seed import seed_data


# Module-level application logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    notification_task = None

    if os.getenv("SKIP_DB_STARTUP") == "1":
        logger.info("SKIP_DB_STARTUP=1 set. Skipping DB startup checks and seeding.")
        yield
        if notification_task:
            notification_task.cancel()
            try:
                await notification_task
            except asyncio.CancelledError:
                pass
        return

    from app.models import registry  # noqa: F401

    logger.info("Starting up... waiting for database...")
    db_connected = False
    
    # Wait for the database to accept connections; Alembic manages the schema.
    for i in range(15):
        try:
            with engine.connect():
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

    # Seed reference data only after the database is reachable.
    try:
        seed_data()
    except Exception as e:
        logger.warning("Seeding warning: %s", e)

    if settings.NOTIFICATION_WORKER_ENABLED:
        try:
            if inspect(engine).has_table("notifications"):
                notification_task = asyncio.create_task(_run_notification_worker())
                logger.info("Notification worker started.")
            else:
                logger.warning(
                    "Notification worker disabled because the notifications table is missing."
                )
        except Exception as exc:
            logger.warning("Notification worker startup skipped: %s", exc)

    yield

    # Cancel background jobs during shutdown.
    if notification_task:
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

async def _run_notification_worker():
    from app.core.database import SessionLocal
    from app.services.notification_service import notification_service

    while True:
        await asyncio.sleep(settings.NOTIFICATION_POLL_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            notification_service.process_pending_notifications(
                db,
                batch_size=settings.NOTIFICATION_BATCH_SIZE,
            )
        except OperationalError as exc:
            logger.debug("Notification worker skipped: %s", exc)
            db.rollback()
        except Exception as exc:
            logger.error("Notification worker error: %s", exc)
            db.rollback()
        finally:
            db.close()

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
    
    # Allow local frontend development and the deployed web app.
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

    @application.get("/")
    def root():
        return {
            "service": "occacia-backend",
            "status": "ok",
            "docs": "/api/docs",
        }
    
    add_exception_handlers(application)
    application.include_router(api_router)
    return application

app = create_app()
