# backend/app/routers/admin_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_admin as get_current_admin_user
from app.models.user import User
from app.schemas.vendor_schema import (
    OrganizationResponse, OrganizationDetailResponse, OrganizationListResponse,
    OrganizationStatusUpdate,
    OrganizationFilter, OrganizationStatus
)
from app.services.organization_service import VendorService

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependency
def get_vendor_service(db: Session = Depends(get_db)):
    return VendorService(db)

# ==================== ORGANIZATION ENDPOINTS ====================

@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[OrganizationStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    List all organizations with filtering and pagination.
    """
    filters = OrganizationFilter(
        status=status,
        search=search
    )
    
    organizations, total = vendor_service.get_organizations(
        skip=skip, limit=limit, filters=filters
    )
    
    return OrganizationListResponse(
        items=[OrganizationResponse.model_validate(o) for o in organizations],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )

@router.get("/organizations/{org_id}", response_model=OrganizationDetailResponse)
async def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Get detailed information about a specific organization.
    """
    org = vendor_service.get_organization_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return OrganizationDetailResponse.model_validate(org)

@router.put("/organizations/{org_id}/status", response_model=OrganizationResponse)
async def update_organization_status(
    org_id: int,
    status_update: OrganizationStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Update organization approval status (pending, approved, rejected).
    """
    org = vendor_service.update_organization_status(
        org_id=org_id,
        status_update=status_update,
        reviewed_by=current_admin.id
    )
    return OrganizationResponse.model_validate(org)

@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Delete an organization (admin only).
    """
    vendor_service.delete_organization(org_id)
    return {"message": "Organization deleted successfully"}
