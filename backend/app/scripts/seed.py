from __future__ import annotations

import logging
from datetime import timedelta

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
            {"email": "boss@occacia.com"},
            {
                "admin_id": generate_prefixed_id("ADM"),
                "password_hash": get_password_hash("SuperSecretPassword123!"),
                "staff_role": "super_admin",
                "status": "ACTIVE"
            },
        )
        created_rows += int(created)

        # ── 2. The Test Customer ─────────────────────────────────────────────────────
        customer1, created = _get_or_create(
            db,
            Customer,
            {"email": "kashmikat@gmail.com"},
            {
                "customer_id": generate_prefixed_id("CUS"),
                "full_name": "Kashmika De Silva",
                "password_hash": get_password_hash("testpass1"),
                "phone": "+94771111000",
                "locale": "en-LK",
                "address": "Colombo, Sri Lanka",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        # ── 3. Sri Lankan Vendors (High, Medium, and Budget Tiers) ─────────────────
        
        # VENDOR: Galle Face Hotel (Venue - Premium)
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

        # VENDOR: Mount Lavinia Hotel (Venue - Medium/High)
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

        # VENDOR: Colombo Jazz Quintet (Music - Premium)
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

        # VENDOR: Daddy Live Band (Music - High Energy)
        vendor_music_2, created = _get_or_create(
            db, Vendor, {"email": "contact@daddyband.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Daddy Band",
                "display_name": "Daddy Live Band",
                "location_base": "Colombo",
                "phone": "+94778889999",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # VENDOR: The Fab (Bakery - Medium/Premium)
        vendor_bakery, created = _get_or_create(
            db, Vendor, {"email": "orders@thefab.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "The Fab",
                "display_name": "The Fab Bakery",
                "location_base": "Colombo",
                "phone": "+94112555666",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # VENDOR: Sponge (Bakery - Budget/Medium)
        vendor_bakery_2, created = _get_or_create(
            db, Vendor, {"email": "sales@sponge.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Sponge Pastry Shop",
                "display_name": "Sponge Bakery",
                "location_base": "Colombo 03",
                "phone": "+94112345678",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # VENDOR: Flash Moments (Photography - Premium)
        vendor_photo, created = _get_or_create(
            db, Vendor, {"email": "hello@flashmoments.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Flash Moments Photography",
                "display_name": "Flash Moments",
                "location_base": "Kandy",
                "phone": "+94812223344",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # VENDOR: Lassana Flora (Decor/Flowers - Premium)
        vendor_decor, created = _get_or_create(
            db, Vendor, {"email": "info@lassana.com"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Lassana Flora",
                "display_name": "Lassana Flora Events",
                "location_base": "Colombo",
                "phone": "+94112002000",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)

        # VENDOR: Tasty Caterers (Catering - Budget/Medium)
        vendor_cater, created = _get_or_create(
            db, Vendor, {"email": "orders@tasty.lk"},
            {
                "vendor_id": generate_prefixed_id("VND"),
                "business_name": "Tasty Caterers",
                "display_name": "Tasty Caterers",
                "location_base": "Colombo 05",
                "phone": "+94112585858",
                "approval_status": "APPROVED",
                "is_verified": True,
                "password_hash": get_password_hash("Vendor123!"),
            }
        )
        created_rows += int(created)


        # ── 4. LKR Offerings (The Supermarket Inventory) ────────────────────────────
        
        # --- VENUES ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_hotel.vendor_id, "name": "Grand Ballroom"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "VENUE",
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
            db, Offering, {"vendor_id": vendor_hotel_2.vendor_id, "name": "Beachfront Pavilion"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "VENUE",
                "description": "Beautiful outdoor beachfront space for private events.",
                "price": 300000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "MEDIUM",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        # --- MUSIC & ENTERTAINMENT ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_music.vendor_id, "name": "Live Jazz Band (4 Hours)"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "DJ & MUSIC",
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

        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_music_2.vendor_id, "name": "Pop & Baila Party Band"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "BAND & LIVE MUSIC",
                "description": "High energy band playing local and international hits.",
                "price": 150000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "MEDIUM",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        # --- CAKES & BAKERY ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_bakery.vendor_id, "name": "Custom 3-Tier Fondant Cake"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "CAKES & BAKERY",
                "description": "Beautiful custom designed cake for luxury celebrations.",
                "price": 28000.0,
                "currency": "LKR",
                "unit": "item",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_bakery_2.vendor_id, "name": "Classic Ribbon Cake (2KG)"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "CAKES & BAKERY",
                "description": "Delicious standard ribbon cake with buttercream icing.",
                "price": 7500.0,
                "currency": "LKR",
                "unit": "item",
                "quality_tier": "LOW", # Will be picked up by the Budget package!
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        # --- CATERING ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_cater.vendor_id, "name": "Standard Sri Lankan Buffet"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "CATERING",
                "description": "Authentic rice and curry buffet with 5 curries and dessert.",
                "price": 4500.0,
                "currency": "LKR",
                "unit": "head",
                "quality_tier": "LOW", # Will be picked up by the Budget package!
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)

        # --- DECOR & FLOWERS ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_decor.vendor_id, "name": "Elegant Floral Centerpieces"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "FLORAL ARRANGEMENTS",
                "description": "Fresh imported flowers arranged for 10 tables.",
                "price": 45000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
            }
        )
        created_rows += int(created)
        
        # --- PHOTOGRAPHY ---
        _, created = _get_or_create(
            db, Offering, {"vendor_id": vendor_photo.vendor_id, "name": "Full Event Coverage"},
            {
                "offering_id": generate_prefixed_id("OFF"),
                "category": "PHOTOGRAPHY & VIDEOGRAPHY",
                "description": "Unlimited photos and cinematic video for the entire event.",
                "price": 120000.0,
                "currency": "LKR",
                "unit": "event",
                "quality_tier": "HIGH",
                "is_active": True,
                "is_available": True,
            }
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