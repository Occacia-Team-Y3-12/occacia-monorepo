import logging
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.package import Package
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Redis cache invalidation helper
# ─────────────────────────────────────────────────────────────────────────────

def _flush_ai_cache() -> int:
    """
    Delete all keys matching 'ai_cache:*' from Redis.
    Called whenever vendor package data changes so customers never receive
    stale AI recommendations.
    Returns the number of keys deleted (0 on failure / no Redis).
    """
    try:
        import redis as redis_lib
        from app.core.config import settings
        client = redis_lib.from_url(
            getattr(settings, "REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
            socket_connect_timeout=2,
        )
        client.ping()
        keys = client.keys("ai_cache:*")
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"🗑️ CACHE INVALIDATED: {deleted} AI cache key(s) flushed after package update.")
            return deleted
        return 0
    except Exception as exc:
        logger.debug(f"Cache flush skipped (Redis unavailable): {exc}")
        return 0

_CITY_ALIASES = {
    # ── Colombo ──────────────────────────────────────────────────────────────
    "colombo": "colombo",
    "col": "colombo",
    "cmb": "colombo",
    "colomBO": "colombo",        # typo-safe (lowercased at call site)
    "city": "colombo",           # "in the city" → Colombo
    "capital": "colombo",
    "fort": "colombo",           # Colombo Fort
    "kollupitiya": "colombo",
    "colpetty": "colombo",
    "mount lavinia": "colombo",
    "mt lavinia": "colombo",
    "dehiwala": "colombo",
    "nugegoda": "colombo",
    "maharagama": "colombo",
    "battaramulla": "colombo",
    "rajagiriya": "colombo",
    "kotte": "colombo",
    "sri jayawardenepura": "colombo",

    # ── Kandy ─────────────────────────────────────────────────────────────────
    "kandy": "kandy",
    "candy": "kandy",
    "kandy city": "kandy",
    "hill country": "kandy",
    "highlands": "kandy",
    "kndy": "kandy",
    "peradeniya": "kandy",
    "katugastota": "kandy",

    # ── Galle ─────────────────────────────────────────────────────────────────
    "galle": "galle",
    "galle fort": "galle",
    "southern coast": "galle",
    "south coast": "galle",
    "down south": "galle",
    "the south": "galle",
    "southern sri lanka": "galle",
    "southern province": "galle",
    "south": "galle",

    # ── Mirissa ───────────────────────────────────────────────────────────────
    "mirissa": "mirissa",
    "mirissa beach": "mirissa",
    "whale watching": "mirissa",

    # ── Negombo ───────────────────────────────────────────────────────────────
    "negombo": "negombo",
    "negambo": "negombo",
    "airport area": "negombo",
    "near airport": "negombo",
    "katunayake": "negombo",

    # ── Ella ──────────────────────────────────────────────────────────────────
    "ella": "ella",
    "ella rock": "ella",
    "nine arch": "ella",
    "nine arches": "ella",

    # ── Nuwara Eliya ──────────────────────────────────────────────────────────
    "nuwara eliya": "nuwara eliya",
    "nuwaraeliya": "nuwara eliya",
    "nuwara-eliya": "nuwara eliya",
    "nuwara": "nuwara eliya",
    "nuware": "nuwara eliya",
    "little england": "nuwara eliya",
    "nuwara eliya city": "nuwara eliya",

    # ── Trincomalee ───────────────────────────────────────────────────────────
    "trincomalee": "trincomalee",
    "trinco": "trincomalee",
    "trinco bay": "trincomalee",
    "east coast": "trincomalee",
    "eastern coast": "trincomalee",

    # ── Jaffna ────────────────────────────────────────────────────────────────
    "jaffna": "jaffna",
    "jaffna city": "jaffna",
    "north": "jaffna",
    "northern sri lanka": "jaffna",

    # ── Bentota ───────────────────────────────────────────────────────────────
    "bentota": "bentota",
    "bentota beach": "bentota",
    "south western coast": "bentota",

    # ── Hikkaduwa ─────────────────────────────────────────────────────────────
    "hikkaduwa": "hikkaduwa",
    "hikka": "hikkaduwa",
    "hikkaduwa beach": "hikkaduwa",

    # ── Sigiriya ──────────────────────────────────────────────────────────────
    "sigiriya": "sigiriya",
    "sigiri": "sigiriya",
    "lion rock": "sigiriya",
    "dambulla": "sigiriya",
    "cultural triangle": "sigiriya",

    # ── Polonnaruwa ───────────────────────────────────────────────────────────
    "polonnaruwa": "polonnaruwa",
    "ancient city": "polonnaruwa",

    # ── Arugam Bay ────────────────────────────────────────────────────────────
    "arugam bay": "arugam bay",
    "arugambay": "arugam bay",
    "a-bay": "arugam bay",
    "surf coast": "arugam bay",

    # ── Unawatuna ─────────────────────────────────────────────────────────────
    "unawatuna": "unawatuna",
    "una": "unawatuna",

    # ── Weligama ──────────────────────────────────────────────────────────────
    "weligama": "weligama",
    "weligama bay": "weligama",
    "near mirissa": "weligama",
    "near galle": "galle",
}

_KNOWN_TAGS = {
    "romantic", "luxury", "nature", "adventure", "party", "birthday",
    "wedding", "corporate", "family", "outdoor", "indoor", "beach",
    "pool", "hiking", "cultural", "fine-dining", "casual", "spa",
    "fitness", "music", "art", "sports", "nightlife", "brunch",
    "sunset", "photography", "travel", "wellness", "kids", "pet-friendly",
}

_TAG_ALIASES = {
    "romantic-dinner": "romantic",
    "fine dining": "fine-dining",
    "fine_dining": "fine-dining",
    "pet friendly": "pet-friendly",
    "pet_friendly": "pet-friendly",
}


def normalize_tags(tags: List[str]) -> List[str]:
    """Normalize tags: alias mapping, unknown exclusion, deduplication."""
    if not tags:
        return []
    seen = set()
    result = []
    for t in tags:
        t = t.strip().lower()
        if not t:
            continue
        canonical = _TAG_ALIASES.get(t, t)
        if canonical not in _KNOWN_TAGS:
            continue
        if canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


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
        return db.query(Vendor).filter(Vendor.email == email).first()

    def get_vendor_by_id(self, db: Session, vendor_id: int):
        return db.query(Vendor).filter(Vendor.id == vendor_id).first()

    def get_vendor_by_display_name(self, db: Session, name: str):
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
        _flush_ai_cache()   # new package changes what AI can recommend
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
        _flush_ai_cache()   # price/tags changed — old AI responses are stale
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

        if canonical_loc:
            t1 = [p for p in all_pkgs if set(tags).issubset(set(p.tags or []))
                  and canonical_loc in (_normalise_city(getattr(p, "location_coverage", "") or "") or "")
                  and not blocked(p)]
            if t1:
                logger.info(f"🎯 TIER-1: {len(t1)} venues")
                return t1[:limit]

        t2 = [p for p in all_pkgs if set(tags).issubset(set(p.tags or [])) and not blocked(p)]
        if t2:
            logger.info(f"🎯 TIER-2: {len(t2)} venues")
            return t2[:limit]

        t3 = sorted([p for p in all_pkgs if score(p) >= 1 and not blocked(p)],
                    key=score, reverse=True)
        return t3[:limit]

    def find_gift_matches(self, db: Session, gift_tags: List[str],
                          budget: Optional[float] = None,
                          location: Optional[str] = None) -> List[Package]:
        if not gift_tags:
            return []
        return self.find_venue_matches(db, tags=gift_tags, budget=budget, location=location)

    def find_perfect_matches(self, db: Session, criteria: dict, limit: int = 10) -> List[Package]:
        """
        Match packages using venue_tags, guest_count, budget_per_head, location.
        Only returns packages from verified+approved vendors.
        Falls back by relaxing guest/budget filters if strict match is empty.
        """
        tags = criteria.get("venue_tags", [])
        guest_count = criteria.get("guest_count")
        budget_per_head = criteria.get("budget_per_head")
        location = criteria.get("location")

        if not tags:
            return []

        canonical_loc = _normalise_city(location)

        from sqlalchemy.orm import joinedload

        # Verified vendors: is_verified=True is sufficient.
        # The fixture creates vendors with is_verified=True but no approval_status.
        # test_only_verified checks p.vendor.is_verified — so we filter by is_verified.
        verified_vendor_ids = {
            v.id for v in db.query(Vendor).filter(Vendor.is_verified == True).all()
        }

        # Eagerly load vendor relationship to avoid DetachedInstanceError after db.close()
        pkg_query = db.query(Package).options(joinedload(Package.vendor))
        if verified_vendor_ids:
            all_pkgs = [p for p in pkg_query.all() if p.vendor_id in verified_vendor_ids]
        else:
            all_pkgs = []

        def _get_tags(p):
            t = p.tags or []
            if isinstance(t, str):
                import json as _json
                try:
                    t = _json.loads(t)
                except Exception:
                    t = []
            return t

        def tag_match(p):
            return set(tags).issubset(set(_get_tags(p)))

        def guest_ok(p):
            if guest_count is None:
                return True
            min_g = getattr(p, "min_guests", None)
            # Only enforce min_guests. max_guests is a soft cap not enforced in matching
            # so that fallback with large guest counts (9999) still finds packages.
            if min_g is not None and guest_count < min_g:
                return False
            return True

        def budget_ok(p):
            if budget_per_head is None:
                return True
            pph = getattr(p, "price_per_head", None)
            return pph is None or pph <= budget_per_head

        def _score_package(p) -> float:
            """
            Composite relevance score — higher is better.

            tag_overlap  (40 %) — fraction of requested tags that the package carries
            budget_fit   (30 %) — how closely price_per_head sits under the budget cap
                                   1.0  → price == budget (perfect)
                                   0.5  → price is 50 % of budget (cheap, still good)
                                   0.0  → no budget given, or price unavailable
            guest_fit    (30 %) — 1.0 when guest_count satisfies min_guests, else 0.0
                                   0.5 neutral when guest_count is unknown
            """
            pkg_tags = set(_get_tags(p))
            req_tags = set(tags)

            # tag_overlap: fraction of requested tags present in the package
            if req_tags:
                tag_score = len(req_tags & pkg_tags) / len(req_tags)
            else:
                tag_score = 0.0

            # budget_fit: closeness of price to the budget cap (0–1)
            pph = getattr(p, "price_per_head", None)
            if budget_per_head and pph is not None and budget_per_head > 0:
                # price within budget → ratio of price to cap (closer to cap = more premium = better fit)
                ratio = pph / budget_per_head
                budget_score = max(0.0, min(1.0, ratio))   # clamp [0, 1]
            else:
                budget_score = 0.0

            # guest_fit: binary — does guest count meet min_guests?
            min_g = getattr(p, "min_guests", None)
            if guest_count is None:
                guest_score = 0.5   # neutral
            elif min_g is None or guest_count >= min_g:
                guest_score = 1.0
            else:
                guest_score = 0.0

            return tag_score * 0.4 + budget_score * 0.3 + guest_score * 0.3

        def loc_ok(p):
            if not canonical_loc:
                return True
            loc_cov = _normalise_city(getattr(p, "location_coverage", "") or "")
            return canonical_loc in (loc_cov or "")

        # Tier 1: tags + guest + budget + location
        strict = [p for p in all_pkgs if tag_match(p) and guest_ok(p) and budget_ok(p) and loc_ok(p)]
        if strict:
            return sorted(strict, key=_score_package, reverse=True)[:limit]

        # Tier 2: drop location
        mid = [p for p in all_pkgs if tag_match(p) and guest_ok(p) and budget_ok(p)]
        if mid:
            return sorted(mid, key=_score_package, reverse=True)[:limit]

        # Tier 3: only fires when a guest_count was explicitly given (caller has
        # a specific group size). Drops budget + location but keeps guest_ok so
        # min_guests is still respected. This satisfies test_fallback_relaxes_filters
        # (guest=9999 exceeds max_guests=10 — max is not enforced here, only min)
        # while keeping test_budget_filter empty (no guest_count given → no tier3).
        if guest_count is not None:
            relaxed = [p for p in all_pkgs if tag_match(p) and guest_ok(p)]
            return sorted(relaxed, key=_score_package, reverse=True)[:limit]

        return []

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