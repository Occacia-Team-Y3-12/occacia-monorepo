# backend/app/services/vendor_service.py

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from fastapi import HTTPException, status

from app.models.marketplace import Vendor, Organization, VendorStatus, OrganizationStatus, VendorType
from app.schemas.vendor_schema import (
    VendorCreate, VendorUpdate, VendorStatusUpdate,
    OrganizationCreate, OrganizationUpdate, OrganizationStatusUpdate,
    VendorFilter, OrganizationFilter
)

class VendorService:
    def __init__(self, db: Session):
        self.db = db

    # Vendor Methods
    def get_vendors(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[VendorFilter] = None
    ) -> tuple[List[Vendor], int]:
        query = self.db.query(Vendor)
        
        if filters:
            if filters.status:
                query = query.filter(Vendor.status == filters.status)
            if filters.vendor_type:
                query = query.filter(Vendor.vendor_type == filters.vendor_type)
            if filters.search:
                search_filter = or_(
                    Vendor.business_name.ilike(f"%{filters.search}%"),
                    Vendor.business_email.ilike(f"%{filters.search}%"),
                    Vendor.business_phone.ilike(f"%{filters.search}%")
                )
                query = query.filter(search_filter)
        
        total = query.count()
        vendors = query.order_by(desc(Vendor.created_at)).offset(skip).limit(limit).all()
        return vendors, total

    def get_vendor_by_id(self, vendor_id: int) -> Optional[Vendor]:
        return self.db.query(Vendor).options(
            joinedload(Vendor.organization)
        ).filter(Vendor.id == vendor_id).first()

    def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        db_vendor = Vendor(**vendor_data.model_dump())
        self.db.add(db_vendor)
        self.db.commit()
        self.db.refresh(db_vendor)
        return db_vendor

    def update_vendor(self, vendor_id: int, vendor_data: VendorUpdate) -> Vendor:
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)
        
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def update_vendor_status(
        self,
        vendor_id: int,
        status_update: VendorStatusUpdate,
        reviewed_by: int
    ) -> Vendor:
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        vendor.status = status_update.status
        vendor.status_reason = status_update.status_reason
        vendor.reviewed_by = reviewed_by
        vendor.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def delete_vendor(self, vendor_id: int) -> None:
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        self.db.delete(vendor)
        self.db.commit()

    # Organization Methods
    def get_organizations(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[OrganizationFilter] = None
    ) -> tuple[List[Organization], int]:
        query = self.db.query(Organization)
        
        if filters:
            if filters.status:
                query = query.filter(Organization.status == filters.status)
            if filters.search:
                search_filter = or_(
                    Organization.name.ilike(f"%{filters.search}%"),
                    Organization.legal_name.ilike(f"%{filters.search}%"),
                    Organization.email.ilike(f"%{filters.search}%"),
                    Organization.registration_number.ilike(f"%{filters.search}%")
                )
                query = query.filter(search_filter)
        
        total = query.count()
        organizations = query.order_by(desc(Organization.created_at)).offset(skip).limit(limit).all()
        return organizations, total

    def get_organization_by_id(self, org_id: int) -> Optional[Organization]:
        return self.db.query(Organization).options(
            joinedload(Organization.vendors)
        ).filter(Organization.id == org_id).first()

    def create_organization(self, org_data: OrganizationCreate) -> Organization:
        db_org = Organization(**org_data.model_dump())
        self.db.add(db_org)
        self.db.commit()
        self.db.refresh(db_org)
        return db_org

    def update_organization(self, org_id: int, org_data: OrganizationUpdate) -> Organization:
        org = self.get_organization_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        update_data = org_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(org, field, value)
        
        self.db.commit()
        self.db.refresh(org)
        return org

    def update_organization_status(
        self,
        org_id: int,
        status_update: OrganizationStatusUpdate,
        reviewed_by: int
    ) -> Organization:
        from datetime import datetime
        
        org = self.get_organization_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        org.status = status_update.status
        org.status_reason = status_update.status_reason
        org.reviewed_by = reviewed_by
        org.reviewed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(org)
        return org

    def delete_organization(self, org_id: int) -> None:
        org = self.get_organization_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        self.db.delete(org)
        self.db.commit()

    # Statistics
    def get_pending_counts(self) -> dict:
        vendor_pending = self.db.query(Vendor).filter(
            Vendor.status == VendorStatus.PENDING
        ).count()
        
        org_pending = self.db.query(Organization).filter(
            Organization.status == OrganizationStatus.PENDING
        ).count()
        
        return {
            "vendors_pending": vendor_pending,
            "organizations_pending": org_pending,
            "total_pending": vendor_pending + org_pending
        }