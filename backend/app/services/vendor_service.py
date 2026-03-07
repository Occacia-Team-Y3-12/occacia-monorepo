import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.package import Package
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)

_CITY_ALIASES = {
    "colombo": "colombo", "col": "colombo",
    "kandy": "kandy", "candy": "kandy",
    "galle": "galle", "negombo": "negombo",
    "ella": "ella", "nuwara eliya": "nuwara eliya",
    "nuwaraeliya": "nuwara eliya", "trincomalee": "trincomalee",
    "trinco": "trincomalee", "jaffna": "jaffna",
    "bentota": "bentota", "mirissa": "mirissa", "hikkaduwa": "hikkaduwa",
}


def _normalise_city(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return _CITY_ALIASES.get(raw.strip().lower(), raw.strip().lower())


class VendorService:

    def create_vendor(self, db: Session, vendor_data):
        from app.core.security import get_password_hash
        logger.info(f"🏢 create_vendor: {vendor_data.email} / {vendor_data.business_name}")
        vendor = Vendor(
            email=vendor_data.email,
            password_hash=get_password_hash(vendor_data.password),
            business_name=vendor_data.business_name,
            phone=getattr(vendor_data, "phone", None),
            is_verified=False,
            approval_status="PENDING",
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        logger.info(f"✅ Vendor created: id={vendor.id}")
        return vendor

    def get_vendor_by_email(self, db: Session, email: str):
        logger.debug(f"🔍 get_vendor_by_email: {email}")
        return db.query(Vendor).filter(Vendor.email == email).first()

    def get_vendor_by_id(self, db: Session, vendor_id: int):
        logger.debug(f"🔍 get_vendor_by_id: {vendor_id}")
        return db.query(Vendor).filter(Vendor.id == vendor_id).first()

    def get_vendor_by_display_name(self, db: Session, name: str):
        logger.debug(f"🔍 get_vendor_by_display_name: {name}")
        return db.query(Vendor).filter(Vendor.business_name == name).first()

    def get_all_vendors(self, db: Session):
        return db.query(Vendor).all()

    def get_vendors_by_status(self, db: Session, status: str):
        return db.query(Vendor).filter(Vendor.approval_status == status).all()

    def update_vendor_status(self, db: Session, vendor_id: int, status: str):
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if vendor:
            vendor.approval_status = status
            db.commit()
            db.refresh(vendor)
        return vendor

    def get_packages_by_vendor(self, db: Session, vendor_id: int):
        return db.query(Package).filter(Package.vendor_id == vendor_id).all()

    def get_package_by_id(self, db: Session, package_id: int):
        return db.query(Package).filter(Package.id == package_id).first()

    def create_package(self, db: Session, vendor_id: int, package_data):
        pkg = Package(
            vendor_id=vendor_id,
            name=package_data.name,
            description=getattr(package_data, "description", None),
            price=getattr(package_data, "price", None),
            price_per_head=getattr(package_data, "price_per_head", None),
            tags=getattr(package_data, "tags", []),
            location_coverage=getattr(package_data, "location_coverage", None),
            blocked_dates=getattr(package_data, "blocked_dates", []),
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
        return pkg

    def update_package(self, db: Session, package_id: int, package_data):
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if not pkg:
            return None
        for field in ["name", "description", "price", "price_per_head",
                      "tags", "location_coverage", "blocked_dates"]:
            val = getattr(package_data, field, None)
            if val is not None:
                setattr(pkg, field, val)
        db.commit()
        db.refresh(pkg)
        return pkg

    def delete_package(self, db: Session, package_id: int) -> bool:
        pkg = db.query(Package).filter(Package.id == package_id).first()
        if pkg:
            db.delete(pkg)
            db.commit()
            return True
        return False

    def get_all_packages(self, db: Session, vendor_id: Optional[int] = None):
        q = db.query(Package)
        if vendor_id:
            q = q.filter(Package.vendor_id == vendor_id)
        return q.all()

    def get_all_tags(self, db: Session) -> List[str]:
        packages = db.query(Package).all()
        seen = set()
        tags = []
        for pkg in packages:
            for tag in (pkg.tags or []):
                if tag not in seen:
                    seen.add(tag)
                    tags.append(tag)
        return tags

    def find_venue_matches(self, db: Session, tags: List[str],
                           budget: Optional[float] = None, location: Optional[str] = None,
                           event_date: Optional[date] = None, limit: int = 10) -> List[Package]:
        logger.info(f"🔎 find_venue_matches | tags={tags} budget={budget} location={location} date={event_date}")
        if not tags:
            return []

        canonical_loc = _normalise_city(location)

        q = db.query(Package)
        if budget is not None:
            q = q.filter((Package.price_per_head == None) | (Package.price_per_head <= budget))
        all_pkgs = q.all()
        logger.info(f"📦 Total packages: {len(all_pkgs)}")

        def blocked(p):
            return event_date and event_date in (p.blocked_dates or [])

        def score(p):
            return len(set(tags) & set(p.tags or []))

        # Tier 1: exact + location
        if canonical_loc:
            t1 = [p for p in all_pkgs if set(tags).issubset(set(p.tags or []))
                  and canonical_loc in (_normalise_city(getattr(p, "location_coverage", "") or "") or "")
                  and not blocked(p)]
            if t1:
                logger.info(f"🎯 TIER-1: {len(t1)} venues")
                return t1[:limit]
            logger.info(f"🔶 TIER-1: 0 — trying without location")

        # Tier 2: exact tags
        t2 = [p for p in all_pkgs if set(tags).issubset(set(p.tags or [])) and not blocked(p)]
        if t2:
            logger.info(f"🎯 TIER-2: {len(t2)} venues")
            return t2[:limit]
        logger.info(f"🔶 TIER-2: 0 — trying partial match")

        # Tier 3: partial
        t3 = sorted([p for p in all_pkgs if score(p) >= 1 and not blocked(p)],
                    key=score, reverse=True)
        if t3:
            logger.info(f"⚠️ TIER-3: {len(t3)} partial venues")
        else:
            logger.warning(f"❌ No venues at any tier for tags={tags}")
        return t3[:limit]

    def find_gift_matches(self, db: Session, gift_tags: List[str],
                          budget: Optional[float] = None, location: Optional[str] = None) -> List[Package]:
        if not gift_tags:
            return []
        return self.find_venue_matches(db, tags=gift_tags, budget=budget, location=location)

    def get_availability_block(self, db: Session, tags: List[str], lookahead_days: int = 30) -> str:
        if not tags:
            return ""
        today = date.today()
        window_end = today + timedelta(days=lookahead_days)
        lines = []
        for pkg in db.query(Package).all():
            if not (set(tags) & set(pkg.tags or [])):
                continue
            blocked = [d for d in (pkg.blocked_dates or [])
                       if isinstance(d, date) and today <= d <= window_end]
            if blocked:
                lines.append(f"- '{pkg.name}' NOT available on: {', '.join(str(d) for d in sorted(blocked))}")
        if not lines:
            return ""
        return (f"\n\nVENUE AVAILABILITY — IMPORTANT:\nThese venues have blocked dates "
                f"in the next {lookahead_days} days. Do NOT suggest them for those dates:\n"
                + "\n".join(lines) + "\n")

    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        if not text:
            return None
        lower = text.lower()
        for alias in sorted(_CITY_ALIASES.keys(), key=len, reverse=True):
            if alias in lower:
                return _CITY_ALIASES[alias]
        return None


vendor_service = VendorService()

def normalize_tags(tags):
    if not tags:
        return []
    return [t.strip().lower() for t in tags if t.strip()]
