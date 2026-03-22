from fastapi import APIRouter
from .v1 import router as v1_router
from . import vendor_tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(v1_router)
api_router.include_router(vendor_tasks.router)

__all__ = ["api_router"]