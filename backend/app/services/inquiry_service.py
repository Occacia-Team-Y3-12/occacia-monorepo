"""
app/services/inquiry_service.py
UC-30: Handle Inquiries
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inquiry import Inquiry

logger = logging.getLogger(__name__)

VALID_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED"}


class InquiryService:
    def create_inquiry(
        self,
        db: Session,
        user_id: str,
        role: str,
        subject: Optional[str],
        message: str,
    ) -> Inquiry:
        if not message or not message.strip():
            raise HTTPException(status_code=422, detail="message is required")
        inquiry = Inquiry(
            created_by_user_id=str(user_id),
            created_by_role=role,
            subject=subject,
            message=message.strip(),
            status="OPEN",
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        logger.info("Inquiry %s created by %s %s", inquiry.inquiry_id, role, user_id)
        return inquiry

    def list_user_inquiries(
        self,
        db: Session,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Inquiry], Optional[str]]:
        q = db.query(Inquiry).filter(Inquiry.created_by_user_id == str(user_id))
        if status:
            q = q.filter(Inquiry.status == status.upper())
        if cursor:
            q = q.filter(Inquiry.created_at < cursor)
        q = q.order_by(Inquiry.created_at.desc())
        items = q.limit(limit + 1).all()
        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            next_cursor = str(items[-1].created_at.isoformat())
        return items, next_cursor

    def get_user_inquiry(self, db: Session, inquiry_id: str, user_id: str) -> Inquiry:
        inquiry = (
            db.query(Inquiry)
            .filter(
                Inquiry.inquiry_id == inquiry_id,
                Inquiry.created_by_user_id == str(user_id),
            )
            .first()
        )
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        return inquiry

    def list_all_inquiries(
        self,
        db: Session,
        status: Optional[str] = None,
        creator_role: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> Tuple[List[Inquiry], Optional[str]]:
        q = db.query(Inquiry)
        if status:
            q = q.filter(Inquiry.status == status.upper())
        if creator_role:
            q = q.filter(Inquiry.created_by_role == creator_role.upper())
        if cursor:
            q = q.filter(Inquiry.created_at < cursor)
        q = q.order_by(Inquiry.created_at.desc())
        items = q.limit(limit + 1).all()
        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            next_cursor = str(items[-1].created_at.isoformat())
        return items, next_cursor

    def get_inquiry_admin(self, db: Session, inquiry_id: str) -> Inquiry:
        inquiry = db.query(Inquiry).filter(Inquiry.inquiry_id == inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        return inquiry

    def update_inquiry(
        self,
        db: Session,
        inquiry_id: str,
        admin_id: str,
        status: Optional[str],
        admin_reply: Optional[str],
    ) -> Inquiry:
        inquiry = self.get_inquiry_admin(db, inquiry_id)

        if status:
            status_upper = status.upper()
            if status_upper not in VALID_STATUSES:
                raise HTTPException(
                    status_code=422,
                    detail=f"status must be one of {VALID_STATUSES}",
                )
            inquiry.status = status_upper
            if status_upper == "RESOLVED":
                inquiry.resolved_at = datetime.now(timezone.utc)
            inquiry.handled_by_admin_id = str(admin_id)

        if admin_reply is not None:
            inquiry.admin_reply = admin_reply
            inquiry.handled_by_admin_id = str(admin_id)
            if inquiry.status == "OPEN":
                inquiry.status = "IN_PROGRESS"

        db.commit()
        db.refresh(inquiry)
        logger.info(
            "Inquiry %s updated by admin %s -- status=%s",
            inquiry_id,
            admin_id,
            inquiry.status,
        )
        return inquiry


inquiry_service = InquiryService()
