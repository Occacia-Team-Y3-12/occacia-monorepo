from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.offering_schema import OFFERING_CATEGORIES

router = APIRouter(tags=["Metadata"])


@router.get("/offering-categories")
def list_offering_categories():
    return {"items": OFFERING_CATEGORIES}


@router.get("/version")
def get_version(request: Request):
    version = getattr(request.app, "version", None)
    if not version:
        try:
            from app.core.config import settings

            version = getattr(settings, "APP_VERSION", "1.0.0")
        except Exception:
            version = "1.0.0"
    return {"version": version, "commit": None, "builtAt": None}
