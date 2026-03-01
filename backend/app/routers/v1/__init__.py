from fastapi import APIRouter

from . import auth_router, health_router, planning_router

router = APIRouter()

# We attach the individual files to this master v1 router
router.include_router(auth_router.router)
router.include_router(health_router.router)
router.include_router(planning_router.router)

__all__ = ["router"]
