import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])
_STARTED_AT = datetime.now(timezone.utc)


@router.get("/health")
def health_check(request: Request):
    logger.info("Health check endpoint hit.")
    uptime_seconds = int((datetime.now(timezone.utc) - _STARTED_AT).total_seconds())
    version = getattr(request.app, "version", None) or "1.0.0"
    return {
        "status": "active",
        "system": "Occacia Core",
        "version": version,
        "uptimeSeconds": max(0, uptime_seconds),
    }
