from __future__ import annotations

import logging
import random
from datetime import timedelta

from faker import Faker
from sqlalchemy import inspect, text

from app.common.utils import now_utc, generate_prefixed_id
from app.core.database import Base, SessionLocal
from app.core.security import get_password_hash
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
fake = Faker()

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

# 🔥 EXACT system categories needed by Occi and the Recommendation Engine
VENDOR_CATEGORIES = [
    "cakes & bakery",
    "catering",
    "drinks & bar",
    "dj & music",
    "photography & videography",
    "band & live music",
    "entertainment",
    "floral arrangements",
    "event decoration",
    "venue & spaces",
    "transport",
]

QUALITY_TIERS = ["LOW", "MEDIUM", "HIGH"]

LOCATIONS = [
    "Colombo", "Kandy", "Galle", "Negombo", "Matara",
    "Kurunegala", "Anuradhapura", "Jaffna"
]

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

        def _is_integer_column(table_name: str, column_name: str) -> bool:
            if not inspector.has_table(table_name):
                return False
            for column in inspector.get_columns(table_name):
                if column.get("name") != column_name:
                    continue
                return "INT" in str(column.get("type", "")).upper()
            return False

        required_tables = [model.__tablename__ for model in SEED_MODELS]
        missing_tables = [table for table in required_tables if not inspector.has_table(table)]
        if missing_tables:
            logger.warning(
                "Required tables are missing: %s. "
                "Attempting fail-safe table creation before seeding.",
                ", ".join(sorted(missing_tables)),
            )
            tables_to_create = [
                Base.metadata.tables[table]
                for table in missing_tables
                if table in Base.metadata.tables
            ]
            if tables_to_create:
                if not hasattr(db.bind, "_run_ddl_visitor"):
                    logger.warning("Skipping seed because DB bind does not support DDL create_all in this context.")
                    return False
                Base.metadata.create_all(bind=db.bind, tables=tables_to_create)
                inspector = inspect(db.bind)
                still_missing = [
                    table for table in required_tables if not inspector.has_table(table)
                ]
                if still_missing:
                    logger.warning("Skipping seed because required tables are still missing after fail-safe creation.")
                    return False
            else:
                return False

        # [FAIL-SAFE] Ensure critical columns exist on existing databases.
        table_column_failsafes: dict[str, list[tuple[str, str]]] = {
            "offerings": [
                ("quality_tier", "ALTER TABLE offerings ADD COLUMN IF NOT EXISTS quality_tier VARCHAR NOT NULL DEFAULT 'MEDIUM'"),
                ("created_at", "ALTER TABLE offerings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
            ],
            "customers": [
                ("password_reset_token", "ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR"),
                ("password_reset_token_expires_at", "ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_reset_token_expires_at TIMESTAMP WITH TIME ZONE"),
            ],
            "vendors": [
                ("display_name", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS display_name VARCHAR"),
                ("contact_phone", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contact_phone VARCHAR"),
                ("organization_id", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS organization_id INTEGER"),
                ("approval_status", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'PENDING'"),
                ("approved_at", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE"),
                ("password_reset_token", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR"),
                ("password_reset_token_expires_at", "ALTER TABLE vendors ADD COLUMN IF NOT EXISTS password_reset_token_expires_at TIMESTAMP WITH TIME ZONE"),
            ],
        }

        for table_name, column_specs in table_column_failsafes.items():
            if not inspector.has_table(table_name):
                continue
            columns = {c["name"] for c in inspector.get_columns(table_name)}
            missing_specs = [(col, ddl) for col, ddl in column_specs if col not in columns]
            if missing_specs:
                with db.bind.begin() as conn:
                    for _, ddl in missing_specs:
                        conn.execute(text(ddl))

        inspector = inspect(db.bind)
        now = now_utc()
        created_rows = 0

        # ── 1. The Master Admin ──────────────────────────────────────────────────────
        admin, created = _get_or_create(
            db,
            Admin,
            {"email": "kashmikat@gmail.com"},
            {
                "admin_id": generate_prefixed_id("ADM"),
                "password_hash": get_password_hash("SuperSecretPassword123!"),
                "staff_role": "super_admin",
                "status": "ACTIVE"
            },
        )
        created_rows += int(created)

        # ── 3. Specific Hand-Crafted Vendors ─────────────────────────────────────────
        vendor_hotel, created = _get_or_create(
            db, Vendor, {"email": "events@gallefacehotel.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Galle Face Hotel",
                "display_name": "Galle Face Hotel",
                "location_base": "Colombo 03",
                "phone": "+94112541010",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        vendor_hotel_2, created = _get_or_create(
            db, Vendor, {"email": "weddings@mountlaviniahotel.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Mount Lavinia Hotel",
                "display_name": "Mount Lavinia Hotel",
                "location_base": "Mount Lavinia",
                "phone": "+94112711711",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        vendor_music, created = _get_or_create(
            db, Vendor, {"email": "bookings@colombojazz.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Colombo Jazz Quintet",
                "display_name": "Colombo Jazz Quintet",
                "location_base": "Colombo",
                "phone": "+94773334444",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # ── 4. Specific Hand-Crafted Offerings ───────────────────────────────────────
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_hotel.vendor_id, "name": "Grand Ballroom"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "venue & spaces",
                "description": "Historic grand ballroom with premium facilities.",
                "price": 500000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_music.vendor_id, "name": "Live Jazz Band (4 Hours)"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "dj & music",
                "description": "Premium 5-piece jazz band for elegant evenings.",
                "price": 85000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)


        # ── 5. 🔥 FAKER: GENERATE 100 REALISTIC VENDORS & OFFERINGS 🔥 ───────────────
        logger.info("Generating 100 extra realistic vendors and offerings...")
        faker_vendors = []
        for i in range(100):
            email = f"vendor{i}_{fake.word()}@occacia.lk"

            vendor, created = _get_or_create(
                db,
                Vendor,
                {"email": email},
                {
                    "vendor_id": generate_prefixed_id("VND"),
                    "business_name": fake.company(),
                    "display_name": fake.company(),
                    "location_base": random.choice(LOCATIONS),
                    "phone": fake.phone_number(),
                    "approval_status": "APPROVED",
                    "is_verified": True,
                    "password_hash": get_password_hash("Vendor123!"),
                },
            )
            created_rows += int(created)
            if created:
                faker_vendors.append(vendor)

        # Generate Offerings for the 100 new vendors
        for vendor in faker_vendors:
            # 1 to 3 offerings per vendor
            for _ in range(random.randint(1, 3)):
                category = random.choice(VENDOR_CATEGORIES)
                quality = random.choice(QUALITY_TIERS)

                base_price = {
                    "LOW": random.randint(5000, 20000),
                    "MEDIUM": random.randint(20000, 80000),
                    "HIGH": random.randint(80000, 300000),
                }[quality]

                _, created = _get_or_create(
                    db,
                    Offering,
                    {
                        "vendor_id": vendor.vendor_id,
                        "name": f"{category.title()} Package - {fake.word().capitalize()}",
                    },
                    {
                        "offering_id": generate_prefixed_id("OFF"),
                        "category": category,
                        "description": fake.sentence(nb_words=12),
                        "price": float(base_price),
                        "currency": "LKR",
                        "unit": "event",
                        "quality_tier": quality,
                        "is_active": True,
                        "is_available": True,
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
        if hasattr(db, "rollback"):
            db.rollback()
        logger.exception("Seed failed due to an unexpected error.")
        raise
    finally:
        if hasattr(db, "close"):
            db.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    seed_data()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())