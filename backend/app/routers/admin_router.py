# backend/app/routers/admin_router.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from app.schemas.vendor_schema import (
    VendorResponse, VendorDetailResponse, VendorListResponse,
    OrganizationResponse, OrganizationDetailResponse, OrganizationListResponse,
    VendorStatusUpdate, OrganizationStatusUpdate,
    VendorFilter, OrganizationFilter, VendorStatus, OrganizationStatus
)
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/admin", tags=["Admin"])

# Dependency
def get_vendor_service(db: Session = Depends(get_db)):
    return VendorService(db)

# ==================== VENDOR ENDPOINTS ====================

@router.get("/vendors", response_model=VendorListResponse)
async def list_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[VendorStatus] = None,
    vendor_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    List all vendors with filtering and pagination.
    Accessible only by admin users.
    """
    filters = VendorFilter(
        status=status,
        vendor_type=vendor_type,
        search=search
    )
    
    vendors, total = vendor_service.get_vendors(skip=skip, limit=limit, filters=filters)
    
    return VendorListResponse(
        items=[VendorResponse.model_validate(v) for v in vendors],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )

@router.get("/vendors/{vendor_id}", response_model=VendorDetailResponse)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Get detailed information about a specific vendor.
    """
    vendor = vendor_service.get_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    return VendorDetailResponse.model_validate(vendor)

@router.put("/vendors/{vendor_id}/status", response_model=VendorResponse)
async def update_vendor_status(
    vendor_id: int,
    status_update: VendorStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Update vendor approval status (pending, approved, rejected).
    """
    vendor = vendor_service.update_vendor_status(
        vendor_id=vendor_id,
        status_update=status_update,
        reviewed_by=current_admin.id
    )
    return VendorResponse.model_validate(vendor)

@router.get("/vendors/stats/pending")
async def get_vendor_pending_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user),
    vendor_service: VendorService = Depends(get_vendor_service)
):
    """
    Get counts of pending vendors and organizations.
    """
    return vendor_service.get_pending_counts()

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