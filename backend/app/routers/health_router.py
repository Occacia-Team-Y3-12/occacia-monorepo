import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    logger.info("Health check endpoint hit.")
    return {"status": "active", "system": "Occacia Core"}
