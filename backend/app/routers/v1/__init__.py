from fastapi import APIRouter
from . import auth_router, health_router, planning_router, persona_router, admin_router, vendor_router

router = APIRouter()

router.include_router(auth_router.router)
router.include_router(health_router.router)
router.include_router(planning_router.router)
router.include_router(persona_router.router)
router.include_router(admin_router.router)
router.include_router(vendor_router.router)

__all__ = ["router"]