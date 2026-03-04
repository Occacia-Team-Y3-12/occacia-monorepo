from fastapi import APIRouter

from .v1 import router as v1_router

# This variable name 'api_router' MUST match what main.py is importing
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(v1_router)

__all__ = ["api_router"]
