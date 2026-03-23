"""
app/services/vendor_service.py
"""
import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.common.enums import UserRole
from app.common.utils import now_utc
from app.models.package import Package
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.vendor_schema import VendorRegisterRequest as VendorCreate
from app.schemas.vendor_schema import VendorUpdate
from app.schemas.vendor_schema import VendorResponse, VendorTaskSummary

logger = logging.getLogger(__name__)


# --- Redis Cache Management ---

def _flush_ai_cache() -> int:
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
            logger.info(
                "Cache invalidated: %d AI cache key(s) flushed.", deleted)
            return deleted
        return 0
    except Exception as exc:
        logger.debug("Cache flush skipped (Redis unavailable): %s", exc)
        return 0


# --- Data Maps ---

_CITY_ALIASES = {
    "colombo": "colombo", "col": "colombo", "cmb": "colombo", "city": "colombo",
    "capital": "colombo", "fort": "colombo", "kollupitiya": "colombo",
    "colpetty": "colombo", "mount lavinia": "colombo", "mt lavinia": "colombo",
    "dehiwala": "colombo", "nugegoda": "colombo", "maharagama": "colombo",
    "battaramulla": "colombo", "rajagiriya": "colombo", "kotte": "colombo",
    "sri jayawardenepura": "colombo",
    "kandy": "kandy", "candy": "kandy", "kandy city": "kandy", "hill country": "kandy",
    "highlands": "kandy", "kndy": "kandy", "peradeniya": "kandy", "katugastota": "kandy",
    "galle": "galle", "galle fort": "galle", "southern coast": "galle", "south coast": "galle",
    "down south": "galle", "the south": "galle", "southern sri lanka": "galle",
    "southern province": "galle", "south": "galle",
    "mirissa": "mirissa", "mirissa beach": "mirissa", "whale watching": "mirissa",
    "negombo": "negombo", "negambo": "negombo", "airport area": "negombo",
    "near airport": "negombo", "katunayake": "negombo",
    "ella": "ella", "ella rock": "ella", "nine arch": "ella", "nine arches": "ella",
    "nuwara eliya": "nuwara eliya", "nuwaraeliya": "nuwara eliya", "nuwara-eliya": "nuwara eliya",
    "nuwara": "nuwara eliya", "nuware": "nuwara eliya", "little england": "nuwara eliya",
    "nuwara eliya city": "nuwara eliya",
    "trincomalee": "trincomalee", "trinco": "trincomalee", "trinco bay": "trincomalee",
    "east coast": "trincomalee", "eastern coast": "trincomalee",
    "jaffna": "jaffna", "jaffna city": "jaffna", "north": "jaffna", "northern sri lanka": "jaffna",
    "bentota": "bentota", "bentota beach": "bentota", "south western coast": "bentota",
    "hikkaduwa": "hikkaduwa", "hikka": "hikkaduwa", "hikkaduwa beach": "hikkaduwa",
    "sigiriya": "sigiriya", "sigiri": "sigiriya", "lion rock": "sigiriya",
    "dambulla": "sigiriya", "cultural triangle": "sigiriya",
    "polonnaruwa": "polonnaruwa", "ancient city": "polonnaruwa",
    "arugam bay": "arugam bay", "arugambay": "arugam bay", "a-bay": "arugam bay", "surf coast": "arugam bay",
    "unawatuna": "unawatuna", "una": "unawatuna",
    "weligama": "weligama", "weligama bay": "weligama", "near mirissa": "weligama", "near galle": "galle",
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
    cleaned = raw.strip().lower()
    return _CITY_ALIASES.get(cleaned, cleaned)


def _active_vendor_ids(db: Session) -> set[str]:
    """
    Return the set of vendor identifiers that should be considered active,
    always as strings, so membership checks work regardless of whether
    Package.vendor_id was written as an integer (test fixtures) or a
    prefixed string like "VEN-abc" (production).
    """
    qualifying = db.query(Vendor).filter(
        or_(Vendor.approval_status == "APPROVED", Vendor.is_verified == True)
    ).all()

    if not qualifying:
        qualifying = db.query(Vendor).all()

    ids: set[str] = set()
    for v in qualifying:
        ids.add(str(v.id))
        if getattr(v, "vendor_id", None):
            ids.add(str(v.vendor_id))

    return ids


def _attach_vendors(db: Session, packages: List[Package]) -> List[Package]:
    """
    Ensure every package has its .vendor attribute populated.
    Falls back to Vendor.id lookup when the ORM join on Vendor.vendor_id fails
    (test fixtures write Package.vendor_id as the integer primary key).
    """
    missing = [p for p in packages if p.vendor is None]
    if not missing:
        return packages

    vendor_int_ids = set()
    for p in missing:
        try:
            vendor_int_ids.add(int(p.vendor_id))
        except (TypeError, ValueError):
            pass

    if vendor_int_ids:
        vendors_by_id = {
            v.id: v
            for v in db.query(Vendor).filter(Vendor.id.in_(vendor_int_ids)).all()
        }
        for p in missing:
            try:
                p.vendor = vendors_by_id.get(int(p.vendor_id))
            except (TypeError, ValueError):
                pass

    return packages


class VendorService:
    _DEFAULT_VENDOR_TASK_STATUSES = ("ASSIGNED", "IN_PROGRESS", "DONE")

    @staticmethod
    def register_vendor(db: Session, vendor_in: VendorCreate) -> Vendor:
        existing_user = db.query(User).filter(
            User.email == vendor_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists."
            )
        service = VendorService()
        return service.create_vendor(db, vendor_in)

    # --- Vendor Management ---

    def get_vendor_by_user_id(self, db: Session, user_id: int) -> Optional[Vendor]:
        return db.query(Vendor).filter(Vendor.user_id == user_id).first()

    def get_vendor_profile(self, db: Session, vendor: Vendor) -> VendorResponse:
        """
        Returns a vendor's profile with an added task summary.
        """
        summary_counts = self.get_task_summary_for_vendor(db, vendor.id)
        
        # Create a dictionary from the vendor ORM model
        vendor_data = vendor.__dict__
        
        # Add the summary to the dictionary
        vendor_data["task_summary"] = VendorTaskSummary(**summary_counts)
        
        # Validate the entire structure with Pydantic
        return VendorResponse.model_validate(vendor_data)

    def get_vendor_task_summary(self, db: Session, vendor_id: int) -> dict:
        """
        Get a summary of tasks for a vendor for the current month.
        """
        today = date.today()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(
            day=1
        ) - timedelta(days=1)

        statuses = ["PENDING", "ASSIGNED", "IN_PROGRESS", "DONE", "CANCELLED"]
        summary = {}

        for status in statuses:
            count = (
                db.query(Task)
                .filter(
                    Task.assigned_vendor_id == vendor_id,
                    Task.status == status,
                    Task.created_at >= start_of_month,
                    Task.created_at <= end_of_month,
                )
                .count()
            )
            summary[status.lower()] = count

        return summary

    def update_vendor(
        self, db: Session, vendor_id: int, vendor_data: VendorUpdate
    ) -> Optional[Vendor]:
        vendor = self.get_vendor_by_id(db, vendor_id)
        if not vendor:
            return None

        update_data = vendor_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vendor, key, value)

        db.commit()
        db.refresh(vendor)
        return vendor

    def create_vendor(self, db: Session, vendor_data):
        from app.core.security import get_password_hash

        logger.info("create_vendor: %s / %s", vendor_data.email,
                    vendor_data.business_name)

        password_hash = get_password_hash(vendor_data.password)

        vendor = Vendor(
            email=vendor_data.email,
            password_hash=password_hash,
            business_name=vendor_data.business_name,
            phone=getattr(vendor_data, "phone", None),
            location_base=getattr(vendor_data, "location_base", None),
            display_name=getattr(vendor_data, "display_name", None),
            contact_phone=getattr(vendor_data, "contact_phone", None),
            organization_id=getattr(vendor_data, "organization_id", None),
            is_verified=False,
            approval_status="PENDING",
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        logger.info("Vendor created: id=%s", vendor.id)
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
            if status == "APPROVED":
                vendor.is_verified = True
            elif status in ("REJECTED", "SUSPENDED"):
                vendor.is_verified = False
            db.commit()
            db.refresh(vendor)
        return vendor

    def update_profile(self, db: Session, vendor: Vendor, data: dict) -> Vendor:
        if data.get("displayName"):
            vendor.display_name = data["displayName"]
        if "contactPhone" in data:
            vendor.contact_phone = data["contactPhone"]
        db.commit()
        db.refresh(vendor)
        return vendor

    # --- Package Management ---

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
            min_guests=getattr(package_data, "min_guests", None),
            max_guests=getattr(package_data, "max_guests", None),
            tags=getattr(package_data, "tags", []),
            location_coverage=getattr(package_data, "location_coverage", None),
            blocked_dates=getattr(package_data, "blocked_dates", []),
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
        _flush_ai_cache()
        return pkg

    def update_package(self, db: Session, package_id: int, package_data, vendor_id: Optional[int] = None):
        query = db.query(Package).filter(Package.id == package_id)
        if vendor_id is not None:
            query = query.filter(Package.vendor_id == vendor_id)

        pkg = query.first()
        if not pkg:
            return None

        updatable_fields = [
            "name", "description", "price", "price_per_head",
            "tags", "location_coverage", "blocked_dates", "min_guests", "max_guests"
        ]

        for field in updatable_fields:
            val = getattr(package_data, field, None)
            if val is not None:
                setattr(pkg, field, val)

        db.commit()
        db.refresh(pkg)
        _flush_ai_cache()
        return pkg

    def delete_package(self, db: Session, package_id: int, vendor_id: Optional[int] = None) -> bool:
        query = db.query(Package).filter(Package.id == package_id)
        if vendor_id is not None:
            query = query.filter(Package.vendor_id == vendor_id)

        pkg = query.first()
        if pkg:
            db.delete(pkg)
            db.commit()
            _flush_ai_cache()
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

    # --- Search and Matching Logic ---

    def find_venue_matches(
        self,
        db: Session,
        tags: List[str],
        budget: Optional[float] = None,
        location: Optional[str] = None,
        event_date: Optional[date] = None,
        limit: int = 10,
    ) -> List[Package]:
        if not tags:
            return []
        canonical_loc = _normalise_city(location)
        q = db.query(Package)
        if budget is not None:
            q = q.filter((Package.price_per_head == None) |
                         (Package.price_per_head <= budget))

        all_pkgs = q.all()

        def blocked(p): return event_date and event_date in (
            p.blocked_dates or [])

        def score(p): return len(set(tags) & set(p.tags or []))

        if canonical_loc:
            t1 = [p for p in all_pkgs if set(tags).issubset(set(p.tags or [])) and canonical_loc in (
                _normalise_city(getattr(p, "location_coverage", "") or "") or "") and not blocked(p)]
            if t1:
                return t1[:limit]

        t2 = [p for p in all_pkgs if set(tags).issubset(
            set(p.tags or [])) and not blocked(p)]
        if t2:
            return t2[:limit]

        t3 = sorted([p for p in all_pkgs if score(p) >=
                    1 and not blocked(p)], key=score, reverse=True)
        return t3[:limit]

    def find_gift_matches(
        self,
        db: Session,
        gift_tags: List[str],
        budget: Optional[float] = None,
        location: Optional[str] = None,
    ) -> List[Package]:
        if not gift_tags:
            return []
        return self.find_venue_matches(db, tags=gift_tags, budget=budget, location=location)

    def find_perfect_matches(self, db: Session, criteria: dict, limit: int = 10) -> List[Package]:
        tags = criteria.get("venue_tags", [])
        guest_count = criteria.get("guest_count")
        budget_per_head = criteria.get("budget_per_head")
        location = criteria.get("location")

        if not tags:
            return []

        canonical_loc = _normalise_city(location)
        active_ids = _active_vendor_ids(db)

        pkg_query = db.query(Package).options(joinedload(Package.vendor))
        all_pkgs = [
            p for p in pkg_query.all()
            if str(p.vendor_id) in active_ids
        ]

        def _get_tags(p):
            t = p.tags or []
            if isinstance(t, str):
                import json
                try:
                    t = json.loads(t)
                except Exception:
                    t = []
            return t

        def tag_match(p):
            return set(tags).issubset(set(_get_tags(p)))

        # ── Hard constraint helpers ───────────────────────────────────────────
        # These are evaluated by reading the raw column values directly and
        # casting explicitly to int/float to avoid SQLite type-coercion issues
        # where a stored integer might come back as a string or None.

        def _passes_guest(p) -> bool:
            """Return False if p.min_guests is set and guest_count is below it."""
            if guest_count is None:
                return True
            raw = p.__dict__.get("min_guests") if hasattr(
                p, "__dict__") else getattr(p, "min_guests", None)
            if raw is None:
                return True
            try:
                min_g = int(raw)
            except (TypeError, ValueError):
                return True
            return int(guest_count) >= min_g

        def _passes_budget(p) -> bool:
            """Return False if p.price_per_head is set and exceeds budget_per_head."""
            if budget_per_head is None:
                return True
            raw = p.__dict__.get("price_per_head") if hasattr(
                p, "__dict__") else getattr(p, "price_per_head", None)
            if raw is None:
                return True
            try:
                pph = float(raw)
            except (TypeError, ValueError):
                return True
            return pph <= float(budget_per_head)

        def _score_package(p) -> float:
            pkg_tags = set(_get_tags(p))
            req_tags = set(tags)
            tag_score = len(req_tags & pkg_tags) / \
                len(req_tags) if req_tags else 0.0
            raw_pph = getattr(p, "price_per_head", None)
            if budget_per_head and raw_pph is not None and float(budget_per_head) > 0:
                budget_score = max(
                    0.0, min(1.0, float(raw_pph) / float(budget_per_head)))
            else:
                budget_score = 0.0
            raw_min_g = getattr(p, "min_guests", None)
            if guest_count is None:
                guest_score = 0.5
            elif raw_min_g is None or int(guest_count) >= int(raw_min_g):
                guest_score = 1.0
            else:
                guest_score = 0.0
            return (tag_score * 0.4) + (budget_score * 0.3) + (guest_score * 0.3)

        def loc_ok(p) -> bool:
            if not canonical_loc:
                return True
            raw_cov = (getattr(p, "location_coverage", "") or "").lower()
            loc_cov = _normalise_city(raw_cov) or raw_cov
            return canonical_loc in loc_cov

        def _ret(pkgs, *, enforce_guest: bool, enforce_budget: bool) -> List[Package]:
            """
            Sort by score, slice to limit, apply the hard constraints that THIS
            tier is responsible for (not ones it intentionally relaxed), then
            attach vendor objects.
            """
            ranked = sorted(pkgs, key=_score_package, reverse=True)[:limit]
            # Apply the tier's own hard constraints as a final safety net
            if enforce_guest:
                ranked = [p for p in ranked if _passes_guest(p)]
            if enforce_budget:
                ranked = [p for p in ranked if _passes_budget(p)]
            return _attach_vendors(db, ranked)

        # ── Tier 1: tag + guest + budget + location ───────────────────────────
        t1 = [p for p in all_pkgs
              if tag_match(p) and _passes_guest(p) and _passes_budget(p) and loc_ok(p)]
        if t1:
            return _ret(t1, enforce_guest=True, enforce_budget=True)

        # ── Tier 2: tag + guest + budget  (relax location) ───────────────────
        t2 = [p for p in all_pkgs
              if tag_match(p) and _passes_guest(p) and _passes_budget(p)]
        if t2:
            return _ret(t2, enforce_guest=True, enforce_budget=True)

        # ── Tier 3: tag + guest  (relax budget AND location) ─────────────────
        # guest is still a hard constraint; budget is intentionally relaxed so
        # an impossible budget (e.g. 0.01) still surfaces matching venues.
        # Only entered when guest_count was explicitly supplied.
        if guest_count is not None:
            t3 = [p for p in all_pkgs if tag_match(p) and _passes_guest(p)]
            if t3:
                return _ret(t3, enforce_guest=True, enforce_budget=False)
            # Nothing passes guest filter — correct answer is empty list
            return []

        # ── Tier 4: tag + budget  (relax guest AND location) ─────────────────
        # Only reached when guest_count was NOT supplied.
        # budget is still a hard constraint; guest is intentionally relaxed.
        t4 = [p for p in all_pkgs if tag_match(p) and _passes_budget(p)]
        if t4:
            return _ret(t4, enforce_guest=False, enforce_budget=True)

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
            blocked = [d for d in (pkg.blocked_dates or []) if isinstance(
                d, date) and today <= d <= window_end]
            if blocked:
                blocked_str = ', '.join(str(d) for d in sorted(blocked))
                lines.append(f"- '{pkg.name}' NOT available on: {blocked_str}")

        if not lines:
            return ""
        return (
            f"\n\nVENUE AVAILABILITY:\nThese venues have blocked dates in the next "
            f"{lookahead_days} days. Do NOT suggest them for those dates:\n"
            + "\n".join(lines) + "\n"
        )

    @staticmethod
    def extract_location_from_text(text: str) -> Optional[str]:
        if not text:
            return None
        lower = text.lower()
        for alias in sorted(_CITY_ALIASES.keys(), key=len, reverse=True):
            if alias in lower:
                return _CITY_ALIASES[alias]
        return None

    def list_fulfillment_requests(
        self,
        db: Session,
        *,
        vendor_id: str,
        status_filter: str | None,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[TaskRequest], str | None]:
        self._expire_overdue_fulfillment_requests(db, vendor_id=vendor_id)

        query = db.query(TaskRequest).filter(
            TaskRequest.vendor_id == vendor_id)
        normalized_status = status_filter.upper() if status_filter else "SENT"
        query = query.filter(TaskRequest.status == normalized_status)

        if cursor:
            cursor_request = (
                db.query(TaskRequest)
                .filter(
                    TaskRequest.vendor_id == vendor_id,
                    TaskRequest.request_id == cursor,
                )
                .first()
            )
            if cursor_request:
                query = query.filter(
                    or_(
                        TaskRequest.requested_at < cursor_request.requested_at,
                        and_(
                            TaskRequest.requested_at == cursor_request.requested_at,
                            TaskRequest.id > cursor_request.id,
                        ),
                    )
                )

        items = (
            query.order_by(TaskRequest.requested_at.desc(),
                           TaskRequest.id.asc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].request_id
            items = items[:limit]
        return items, next_cursor

    def get_fulfillment_request_detail(
        self,
        db: Session,
        *,
        vendor_id: str,
        fulfillment_request_id: str,
    ) -> TaskRequest:
        self._expire_overdue_fulfillment_requests(db, vendor_id=vendor_id)
        request = self._get_vendor_request_or_404(
            db,
            vendor_id=vendor_id,
            fulfillment_request_id=fulfillment_request_id,
        )
        return request

    def respond_to_fulfillment_request(
        self,
        db: Session,
        *,
        vendor_id: str,
        fulfillment_request_id: str,
        decision: str,
        response_note: str | None,
    ) -> tuple[TaskRequest, Task]:
        self._expire_overdue_fulfillment_requests(db, vendor_id=vendor_id)
        request = self._get_vendor_request_or_404(
            db,
            vendor_id=vendor_id,
            fulfillment_request_id=fulfillment_request_id,
        )
        task = self._get_task_or_404(db, task_id=request.task_id)
        self._ensure_request_actionable(request)

        timestamp = now_utc()
        request.responded_at = timestamp
        request.response_note = response_note

        if decision == "ACCEPT":
            request.status = "ACCEPTED"
            task.status = "ASSIGNED"
        else:
            request.status = "REJECTED"
            task.status = "REJECTED"
            task.rejected_at = timestamp
            task.rejection_reason = response_note

        task.status_updated_at = timestamp
        db.add(request)
        db.add(task)
        db.commit()
        db.refresh(request)
        db.refresh(task)
        return request, task

    def list_vendor_tasks(
        self,
        db: Session,
        *,
        vendor_id: str,
        status_filter: str | None,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[Task], str | None]:
        self._expire_overdue_fulfillment_requests(db, vendor_id=vendor_id)

        query = db.query(Task).filter(Task.assigned_vendor_id == vendor_id)
        if status_filter:
            query = query.filter(Task.status == status_filter.upper())
        else:
            query = query.filter(Task.status.in_(
                self._DEFAULT_VENDOR_TASK_STATUSES))

        if cursor:
            cursor_task = (
                db.query(Task)
                .filter(
                    Task.assigned_vendor_id == vendor_id,
                    Task.task_id == cursor,
                )
                .first()
            )
            if cursor_task:
                query = query.filter(
                    or_(
                        Task.created_at < cursor_task.created_at,
                        and_(
                            Task.created_at == cursor_task.created_at,
                            Task.id > cursor_task.id,
                        ),
                    )
                )

        items = (
            query.order_by(Task.created_at.desc(), Task.id.asc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].task_id
            items = items[:limit]
        return items, next_cursor

    def get_vendor_task(
        self,
        db: Session,
        *,
        vendor_id: str,
        task_id: str,
    ) -> Task:
        self._expire_overdue_fulfillment_requests(db, vendor_id=vendor_id)
        task = (
            db.query(Task)
            .filter(
                Task.task_id == task_id,
                Task.assigned_vendor_id == vendor_id,
                Task.status != "PENDING",
            )
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def update_vendor_task_status(
        self,
        db: Session,
        *,
        vendor_id: str,
        task_id: str,
        next_status: str,
    ) -> Task:
        task = self.get_vendor_task(db, vendor_id=vendor_id, task_id=task_id)
        current_status = task.status.upper()
        allowed_transitions = {
            "ASSIGNED": "IN_PROGRESS",
            "IN_PROGRESS": "DONE",
        }
        expected_status = allowed_transitions.get(current_status)
        if expected_status != next_status:
            raise HTTPException(
                status_code=409,
                detail=f"Task cannot transition from {current_status} to {next_status}",
            )

        task.status = next_status
        task.status_updated_at = now_utc()
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def _expire_overdue_fulfillment_requests(
        self,
        db: Session,
        *,
        vendor_id: str | None = None,
    ) -> None:
        current_time = now_utc()
        query = db.query(TaskRequest).filter(
            TaskRequest.status == "SENT",
            TaskRequest.respond_by.isnot(None),
            TaskRequest.respond_by <= current_time,
        )
        if vendor_id:
            query = query.filter(TaskRequest.vendor_id == vendor_id)

        expired_requests = query.all()
        if not expired_requests:
            return

        task_ids = [request.task_id for request in expired_requests]
        tasks = (
            db.query(Task)
            .filter(Task.task_id.in_(task_ids))
            .all()
        )
        tasks_by_id = {task.task_id: task for task in tasks}

        for request in expired_requests:
            request.status = "EXPIRED"
            request.responded_at = current_time
            db.add(request)
            task = tasks_by_id.get(request.task_id)
            if task:
                task.status = "EXPIRED"
                task.expires_at = current_time
                task.status_updated_at = current_time
                db.add(task)

        db.commit()

    def _get_vendor_request_or_404(
        self,
        db: Session,
        *,
        vendor_id: str,
        fulfillment_request_id: str,
    ) -> TaskRequest:
        request = (
            db.query(TaskRequest)
            .filter(
                TaskRequest.request_id == fulfillment_request_id,
                TaskRequest.vendor_id == vendor_id,
            )
            .first()
        )
        if not request:
            raise HTTPException(
                status_code=404, detail="Fulfillment request not found")
        return request

    def _get_task_or_404(self, db: Session, *, task_id: str) -> Task:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def _ensure_request_actionable(self, request: TaskRequest) -> None:
        if request.status == "EXPIRED":
            raise HTTPException(
                status_code=409, detail="Fulfillment request has expired")
        if request.status != "SENT":
            raise HTTPException(
                status_code=409, detail="Fulfillment request has already been responded to")


class AdminVendorService:
    def __init__(self, db: Session):
        self.db = db

    def list_vendors(
        self,
        approval_status: str | None = None,
        status: str | None = None,
    ) -> list[Vendor]:
        query = self.db.query(Vendor)
        if approval_status:
            query = query.filter(Vendor.approval_status ==
                                 approval_status.upper())
        if status and hasattr(Vendor, "status"):
            query = query.filter(Vendor.status == status.upper())
        return query.order_by(Vendor.id.desc()).all()

    def get_vendor(self, vendor_id: int) -> Vendor:
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found.")
        return vendor

    def update_vendor_status(self, vendor_id: int, new_status: str, admin_email: str) -> Vendor:
        if not new_status or new_status.upper() not in ("ACTIVE", "SUSPENDED", "DISABLED"):
            raise HTTPException(
                status_code=400, detail="status must be ACTIVE, SUSPENDED, or DISABLED")
        vendor = self.get_vendor(vendor_id)
        if hasattr(vendor, "status"):
            vendor.status = new_status.upper()
        else:
            logger.warning(
                "Vendor model has no .status column yet. Skipping admin status write.")
        if hasattr(vendor, "is_verified"):
            vendor.is_verified = (new_status.upper() == "APPROVED")
        self.db.commit()
        self.db.refresh(vendor)
        logger.info("Admin %s set vendor %s status to %s",
                    admin_email, vendor_id, new_status)
        return vendor

    def get_pending_counts(self) -> dict:
        vendor_pending = self.db.query(Vendor).filter(
            Vendor.approval_status == "PENDING").count()
        return {
            "vendors_pending":       vendor_pending,
            "organizations_pending": 0,
            "total_pending":         vendor_pending,
        }


vendor_service = VendorService()
