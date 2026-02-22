import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.database import Base, engine
from app.core.exceptions import add_exception_handlers
from app.routers import auth_router
from app.routers import health_router
from app.routers import planning_router
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

    logger.info("Starting up... waiting for database...")

    db_connected = False
    for i in range(15):  # Try 15 times (30 seconds total)
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

    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Occacia Event Backend",
        root_path="/api",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_exception_handlers(application)
    application.include_router(auth_router.router)
    application.include_router(health_router.router)
    application.include_router(planning_router.router)
    return application


app = create_app()
