from fastapi import APIRouter
from . import (
    auth_router,
    admin_router,
    customer_router,
    health_router,
    organization_router,
    persona_router,
    planning_router,
    vendor_router,
)

router = APIRouter()

router.include_router(auth_router.router)              # /auth/customer/* and /auth/vendor/*
router.include_router(admin_router.auth_admin_router)  # /auth/admin/register, /auth/admin/login
router.include_router(admin_router.router)             # /admin/vendors/{id}/approve|reject
router.include_router(customer_router.router)         # /customers/me
router.include_router(vendor_router.router)            # /vendors/me
router.include_router(vendor_router.admin_router)      # /admin/vendors/*
router.include_router(organization_router.router)      # /admin/organizations/*
router.include_router(persona_router.router)           # /customers/personas/*
router.include_router(health_router.router)
router.include_router(planning_router.router)

__all__ = ["router"]
