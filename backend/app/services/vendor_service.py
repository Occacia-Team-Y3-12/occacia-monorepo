from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.package import Package
from app.models.vendor import Vendor


class VendorService:
    
    @staticmethod
    def register_vendor(db: Session, vendor_in: VendorCreate) -> Vendor:
        """
        Logic to handle the creation of a new vendor and their associated user account.
        """
        # checking if the email is already in the 'users' table
        existing_user = db.query(User).filter(User.email == vendor_in.email).first()
        if existing_user:
            # Throw 400 error if email exists
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists."
            )

        #  Create the User record
        user_id = f"USR-{generate_id()}"
        new_user = User(
            id=user_id,
            email=vendor_in.email,
            hashed_password=get_password_hash(vendor_in.password),
            # Explicitly set the role to VENDOR
            role=UserRole.VENDOR,
            # though the Vendor profile logic might restrict access later based on status
            is_active=True 
        )
        # Add the user to the database session (not committed yet)
        db.add(new_user)
        
        # Step 3: Create the Vendor record (The "profile" layer)
        # Generate a unique VEN- prefix ID
        vendor_id = f"VEN-{generate_id()}"
        new_vendor = Vendor(
            id=vendor_id,
            user_id=user_id, # Link this profile to the user we just created
            business_name=vendor_in.business_name,
            contact_name=vendor_in.contact_name,
            phone_number=vendor_in.phone_number,
            description=vendor_in.description,
            website=vendor_in.website,
            # REQUIREMENT: New registrations must always start as 'PENDING' for admin review
            status=VendorStatus.PENDING
        )
        # Add the vendor to the database session
        db.add(new_vendor)
        
        try:
            # Commit both records as a single atomic transaction
            # If either the User or Vendor creation fails, nothing is saved
            db.commit()
            db.refresh(new_vendor)
            return new_vendor
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during registration: {str(e)}"
            )

    
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
