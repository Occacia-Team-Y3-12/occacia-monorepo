from fastapi import APIRouter

from app.routers.v1 import auth_router, health_router, planning_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router.router)
router.include_router(health_router.router)
router.include_router(planning_router.router)
