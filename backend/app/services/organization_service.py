# backend/app/services/organization_service.py

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.vendor_schema import (
    OrganizationCreate, OrganizationUpdate, OrganizationStatusUpdate,
    OrganizationFilter
)


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db

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
        return self.db.query(Organization).filter(Organization.id == org_id).first()

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
        org.status_reason = status_update.reason
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
