"""
app/services/admin_service.py
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vendor import Vendor
from app.services.auth_service import _send_email

logger = logging.getLogger(__name__)

class AdminService:
    def _send_approval_email(self, vendor: Vendor):
        # Your exact email logic here
        pass

    def _send_rejection_email(self, vendor: Vendor, reason: str):
        # Your exact email logic here
        pass

    def get_vendor(self, db: Session, vendor_id: int) -> Vendor:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")
        return vendor

    def list_vendors(self, db: Session, approval_status: Optional[str] = None, vendor_status: Optional[str] = None) -> list[Vendor]:
        query = db.query(Vendor)
        if approval_status:
            query = query.filter(Vendor.approval_status == approval_status.upper())
        if vendor_status:
            query = query.filter(Vendor.status == vendor_status.upper())
        return query.order_by(Vendor.id.desc()).all()

    def update_vendor_status(self, db: Session, vendor_id: int, new_status: str, admin_email: str) -> Vendor:
        if not new_status or new_status.upper() not in ("ACTIVE", "SUSPENDED", "DISABLED"):
            raise HTTPException(status_code=400, detail="status must be ACTIVE, SUSPENDED, or DISABLED")
            
        vendor = self.get_vendor(db, vendor_id)
        vendor.status = new_status.upper() # I removed your hasattr hack. Update your alembic migrations.
        
        db.commit()
        db.refresh(vendor)
        logger.info(f"Admin {admin_email} set vendor {vendor_id} status to {new_status}")
        return vendor

    def approve_vendor(self, db: Session, vendor_id: int, admin_email: str) -> Vendor:
        vendor = self.get_vendor(db, vendor_id)
        if vendor.approval_status == "APPROVED":
            raise HTTPException(status_code=400, detail="Vendor is already approved.")

        vendor.is_verified = True
        vendor.approval_status = "APPROVED"
        vendor.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(vendor)
        
        self._send_approval_email(vendor)
        logger.info(f"Admin {admin_email} approved vendor {vendor_id}")
        return vendor

    def reject_vendor(self, db: Session, vendor_id: int, reason: str, admin_email: str) -> Vendor:
        vendor = self.get_vendor(db, vendor_id)
        if vendor.approval_status == "REJECTED":
            raise HTTPException(status_code=400, detail="Vendor is already rejected.")

        vendor.is_verified = False
        vendor.approval_status = "REJECTED"
        db.commit()
        db.refresh(vendor)
        
        self._send_rejection_email(vendor, reason)
        logger.info(f"Admin {admin_email} rejected vendor {vendor_id}")
        return vendor

admin_service = AdminService()