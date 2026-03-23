from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import inspect, text

from app.common.utils import now_utc
from app.core.database import SessionLocal
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.notification import Notification
from app.models.offering import Offering
from app.models.organization import Organization
from app.models.package import Package
from app.models.package_execution_request import PackageExecutionRequest
from app.models.package_item import PackageItem
from app.models.persona import Persona
from app.models.recommendation_package import RecommendationPackage
from app.models.support_note import SupportNote
from app.models.task import Task
from app.models.task_models import VendorTask, VendorTaskMessage
from app.models.task_recommendation import TaskRecommendation
from app.models.task_request import TaskRequest
from app.models.user import User
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)


SEED_MODELS = (
    Admin,
    User,
    Customer,
    Vendor,
    Organization,
    Event,
    Persona,
    EventPersona,
    Offering,
    Package,
    Task,
    RecommendationPackage,
    TaskRecommendation,
    PackageItem,
    PackageExecutionRequest,
    TaskRequest,
    VendorTask,
    VendorTaskMessage,
    EventChatMessage,
    Notification,
    SupportNote,
)


def _get_or_create(db, model, lookup: dict, values: dict | None = None):
    instance = db.query(model).filter_by(**lookup).first()
    created = False
    if not instance:
        payload = {**lookup, **(values or {})}
        instance = model(**payload)
        db.add(instance)
        db.flush()
        created = True
    return instance, created


def seed_data() -> bool:
    db = SessionLocal()

    try:
        inspector = inspect(db.bind)
        required_tables = [model.__tablename__ for model in SEED_MODELS]
        missing_tables = [table for table in required_tables if not inspector.has_table(table)]
        if missing_tables:
            logger.warning(
                "Skipping seed because required tables are missing: %s. "
                "Run `poetry run alembic upgrade heads` first.",
                ", ".join(sorted(missing_tables)),
            )
            return False

        # [FAIL-SAFE] Ensure offerings table has quality_tier and created_at columns
        # This protects against cases where migrations were skipped or auto-heal didn't update existing tables.
        if inspector.has_table("offerings"):
            columns = [c["name"] for c in inspector.get_columns("offerings")]
            if "quality_tier" not in columns or "created_at" not in columns:
                logger.info("Adding missing columns to offerings table via fail-safe...")
                # Using raw SQL to be dialect-agnostic but targeting Postgres primarily since it's the target env.
                # 'IF NOT EXISTS' is supported by Postgres 9.6+
                with db.bind.begin() as conn:
                    if "quality_tier" not in columns:
                        conn.execute(
                            text(
                                "ALTER TABLE offerings ADD COLUMN IF NOT EXISTS quality_tier VARCHAR NOT NULL DEFAULT 'MEDIUM'"
                            )
                        )
                    if "created_at" not in columns:
                        conn.execute(
                            text(
                                "ALTER TABLE offerings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
                            )
                        )
                # Refresh inspector to reflect changes
                inspector = inspect(db.bind)

        now = now_utc()
        created_rows = 0

        # ── Admins & Users ──────────────────────────────────────────────────────────
        admin, created = _get_or_create(
            db,
            Admin,
            {"email": "seed.admin@occacia.local"},
            {
                "password_hash": "seed_admin_hash",
                "staff_role": "super_admin",
            },
        )
        created_rows += int(created)

        _user_admin, created = _get_or_create(
            db,
            User,
            {"email": "seed.user.admin@occacia.local"},
            {
                "password_hash": "seed_user_admin_hash",
                "role": "ADMIN",
                "status": "ACTIVE",
                "last_login_at": now,
            },
        )
        created_rows += int(created)

        # ── Customers ──────────────────────────────────────────────────────────────
        customer1, created = _get_or_create(
            db,
            Customer,
            {"email": "seed.customer@occacia.local"},
            {
                "full_name": "Seed Customer",
                "password_hash": "seed_customer_hash",
                "phone": "+94771111000",
                "locale": "en-LK",
                "address": "Colombo, Sri Lanka",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        customer2, created = _get_or_create(
            db,
            Customer,
            {"email": "jane.doe@occacia.local"},
            {
                "full_name": "Jane Doe",
                "password_hash": "seed_customer_hash",
                "phone": "+94772223333",
                "locale": "en-US",
                "address": "Kandy, Sri Lanka",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        # ── Vendors ────────────────────────────────────────────────────────────────
        vendor_studio, created = _get_or_create(
            db,
            Vendor,
            {"email": "seed.vendor@occacia.local"},
            {
                "business_name": "Seed Event Studio",
                "display_name": "Seed Event Studio",
                "location_base": "Colombo",
                "phone": "+94112223344",
                "contact_phone": "+94112223344",
                "approval_status": "APPROVED",
                "approved_at": now,
                "is_verified": True,
                "password_hash": "seed_vendor_hash",
            },
        )
        created_rows += int(created)

        vendor_decor, created = _get_or_create(
            db,
            Vendor,
            {"email": "decor.vendor@occacia.local"},
            {
                "business_name": "Elegant Decorators",
                "display_name": "Elegant Decor",
                "location_base": "Colombo",
                "phone": "+94115556677",
                "contact_phone": "+94115556677",
                "approval_status": "APPROVED",
                "approved_at": now,
                "is_verified": True,
                "password_hash": "seed_vendor_hash",
            },
        )
        created_rows += int(created)

        vendor_photo, created = _get_or_create(
            db,
            Vendor,
            {"email": "photo.vendor@occacia.local"},
            {
                "business_name": "Flash Moments",
                "display_name": "Flash Moments Photography",
                "location_base": "Kandy",
                "phone": "+94812223344",
                "contact_phone": "+94812223344",
                "approval_status": "APPROVED",
                "approved_at": now,
                "is_verified": True,
                "password_hash": "seed_vendor_hash",
            },
        )
        created_rows += int(created)

        # ── Organizations ──────────────────────────────────────────────────────────
        _organization, created = _get_or_create(
            db,
            Organization,
            {"registration_number": "SEED-ORG-001"},
            {
                "name": "Seed Organization",
                "legal_name": "Seed Organization (Pvt) Ltd",
                "tax_id": "TAX-SEED-001",
                "email": "seed.org@occacia.local",
                "phone": "+94112223355",
                "address": "No 100, Flower Road, Colombo",
                "website": "https://seed.occacia.local",
                "description": "Seeded organization for pipeline and QA smoke data.",
                "status": "approved",
                "reviewed_by": admin.id,
                "reviewed_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        created_rows += int(created)

        # ── Offerings ──────────────────────────────────────────────────────────────
        offering_catering, created = _get_or_create(
            db,
            Offering,
            {"vendor_id": vendor_studio.vendor_id, "name": "Seed Deluxe Catering"},
            {
                "category": "CATERING",
                "description": "Premium buffet service for birthday and private events.",
                "price": 8500.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "MEDIUM",
                "is_active": True,
                "is_available": True,
                "updated_at": now,
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            Offering,
            {"vendor_id": vendor_decor.vendor_id, "name": "Basic Floral Setup"},
            {
                "category": "DECOR",
                "description": "Standard floral arrangements for small venues.",
                "price": 15000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "LOW",
                "is_active": True,
                "is_available": True,
                "updated_at": now,
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            Offering,
            {"vendor_id": vendor_decor.vendor_id, "name": "Premium Wedding Backdrop"},
            {
                "category": "DECOR",
                "description": "Luxurious custom backdrop with lighting and silk flowers.",
                "price": 75000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
                "updated_at": now,
            },
        )
        created_rows += int(created)

        # ── Events & Personas ───────────────────────────────────────────────────────
        event_birthday, created = _get_or_create(
            db,
            Event,
            {"customer_id": customer1.customer_id, "title": "Seed Birthday Event"},
            {
                "event_type": "BIRTHDAY",
                "description": "Seeded event used by automated startup pipeline.",
                "location_text": "Colombo 07",
                "start_at": now + timedelta(days=7),
                "end_at": now + timedelta(days=7, hours=4),
                "timezone": "Asia/Colombo",
                "is_all_day": False,
                "status": "CONFIRMED",
                "confirmed_at": now,
            },
        )
        created_rows += int(created)

        event_grad, created = _get_or_create(
            db,
            Event,
            {"customer_id": customer2.customer_id, "title": "Jane's Graduation Party"},
            {
                "event_type": "PARTY",
                "description": "Graduation celebration for friends and family.",
                "location_text": "Grand Hotel, Kandy",
                "start_at": now + timedelta(days=30),
                "end_at": now + timedelta(days=30, hours=5),
                "timezone": "Asia/Colombo",
                "is_all_day": False,
                "status": "DRAFT",
            },
        )
        created_rows += int(created)

        persona, created = _get_or_create(
            db,
            Persona,
            {"customer_id": customer1.customer_id, "name": "Maya Perera"},
            {
                "relationship": "Friend",
                "personality": "Warm, energetic, and enjoys outdoor celebrations.",
                "food_preferences": ["vegetarian", "desserts"],
                "color_preferences": ["gold", "peach"],
                "music_preferences": ["acoustic", "pop"],
                "personality_tags": ["social", "outgoing"],
                "is_confirmed": True,
                "confirmed_at": now,
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            EventPersona,
            {"event_id": event_birthday.event_id, "persona_id": persona.persona_id},
        )
        created_rows += int(created)

        # ── Packages & Tasks ────────────────────────────────────────────────────────
        package, created = _get_or_create(
            db,
            Package,
            {"vendor_id": vendor_studio.vendor_id, "name": "Seed Signature Package"},
            {
                "description": "Core package with catering, decor, and hosting support.",
                "price": 25000.0,
                "price_per_head": 2200.0,
                "min_guests": 10,
                "max_guests": 80,
                "tags": ["catering", "decor", "birthday"],
                "location_coverage": "Colombo",
                "blocked_dates": [],
            },
        )
        created_rows += int(created)

        task, created = _get_or_create(
            db,
            Task,
            {"event_id": event_birthday.event_id, "name": "Arrange Catering"},
            {
                "description": "Arrange and confirm catering menu for guests.",
                "quantity": 1,
                "budget_min": 7000.0,
                "budget_max": 12000.0,
                "currency": "LKR",
                "needs_vendor": "true",
                "status": "ASSIGNED",
                "selected_offering_id": offering_catering.offering_id,
                "assigned_vendor_id": vendor_studio.vendor_id,
                "confirmed_at": now,
                "status_updated_at": now,
                "due_at": now + timedelta(days=5),
            },
        )
        created_rows += int(created)

        # ── Post-Task Entities ─────────────────────────────────────────────────────
        recommendation_package, created = _get_or_create(
            db,
            RecommendationPackage,
            {"event_id": event_birthday.event_id, "package_type": "RECOMMENDED"},
            {
                "package_total_price": 25000.0,
                "currency": "LKR",
                "is_customized": False,
                "base_package_id": f"BASE-PKG-{package.id}",
                "created_by_customer_id": customer1.customer_id,
                "expires_at": now + timedelta(days=2),
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            TaskRecommendation,
            {
                "event_id": event_birthday.event_id,
                "task_id": task.task_id,
                "offering_id": offering_catering.offering_id,
            },
            {
                "score": 0.95,
                "rank": 1,
                "generated_at": now,
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            PackageItem,
            {
                "package_id": recommendation_package.package_id,
                "task_id": task.task_id,
                "offering_id": offering_catering.offering_id,
            },
            {
                "quantity": 1,
                "unit_price": offering_catering.price,
                "line_total": offering_catering.price,
            },
        )
        created_rows += int(created)

        execution_request, created = _get_or_create(
            db,
            PackageExecutionRequest,
            {"idempotency_key": "seed-package-order-001"},
            {
                "event_id": event_birthday.event_id,
                "package_id": recommendation_package.package_id,
                "currency": "LKR",
                "package_total_price": recommendation_package.package_total_price,
                "status": "CREATED",
                "notes": "Seed package execution request.",
                "status_updated_at": now,
            },
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db,
            TaskRequest,
            {
                "package_order_id": execution_request.execution_request_id,
                "task_id": task.task_id,
                "vendor_id": vendor_studio.vendor_id,
                "offering_id": offering_catering.offering_id,
            },
            {
                "status": "ACCEPTED",
                "requested_at": now,
                "respond_by": now + timedelta(days=1),
                "responded_at": now,
                "response_note": "Accepted in seed flow.",
                "attempt_no": 1,
            },
        )
        created_rows += int(created)

        db.commit()
        if created_rows:
            logger.info("Database seeded successfully. Added %s rows.", created_rows)
            return True

        logger.info("Seed script found all records already present. No new rows added.")
        return False
    except Exception:
        db.rollback()
        logger.exception("Seed failed due to an unexpected error.")
        raise
    finally:
        db.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    seed_data()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
