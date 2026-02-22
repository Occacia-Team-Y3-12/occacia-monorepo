from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.package import Package
from app.models.vendor import Vendor


class VendorService:
    def get_vendor_by_email(self, db: Session, email: str) -> Vendor | None:
        return db.query(Vendor).filter(Vendor.email == email).first()

    def get_vendor_by_display_name(self, db: Session, name: str) -> Vendor | None:
        return db.query(Vendor).filter(Vendor.business_name == name).first()

    def create_vendor(self, db: Session, vendor_data: Any) -> Vendor:
        # NOTE: `Vendor` model currently has no `hashed_password` column.
        # We persist only the mapped fields so the endpoint remains functional.
        vendor = Vendor(
            business_name=getattr(vendor_data, "business_name", None)
            or getattr(vendor_data, "display_name", None),
            display_name=getattr(vendor_data, "display_name", None),
            email=vendor_data.email,
            location_base=getattr(vendor_data, "location_base", None) or "Unknown",
            phone=getattr(vendor_data, "phone", None),
            contact_phone=getattr(vendor_data, "contact_phone", None),
            is_verified=False,
            hashed_password=get_password_hash(vendor_data.password)
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    def find_perfect_matches(self, db: Session, analysis: dict) -> list[Package]:
        """
        Takes the AI analysis dictionary and queries the database for matching Packages.
        """
        if not analysis or not isinstance(analysis, dict):
            return []

        missing_info = analysis.get("missing_info", []) or []
        if "SERVICE_UNAVAILABLE" in missing_info:
            return []

        location = analysis.get("location")
        if location == "Any":
            location = None

        budget_per_head = analysis.get("budget_per_head")
        try:
            budget_per_head = float(budget_per_head) if budget_per_head is not None else None
        except (TypeError, ValueError):
            budget_per_head = None

        venue_tags = analysis.get("venue_tags") or []
        if isinstance(venue_tags, str):
            venue_tags = [venue_tags]

        query = db.query(Package).join(Vendor)

        if location:
            query = query.filter(
                or_(
                    Vendor.location_base.ilike(f"%{location}%"),
                    Package.location_coverage.ilike(f"%{location}%"),
                )
            )

        if budget_per_head is not None:
            query = query.filter(
                or_(
                    Package.price_per_head.is_(None),
                    Package.price_per_head <= budget_per_head,
                )
            )

        if venue_tags:
            tag_filters = [Package.tags.contains([t]) for t in venue_tags]
            if tag_filters:
                query = query.filter(or_(*tag_filters))

        return query.limit(5).all()


vendor_service = VendorService()
