from __future__ import annotations

import logging

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

        # ── 1. Admins ────────────────────────────────────────────────────────────────
        admin_primary, created = _get_or_create(
            db,
            Admin,
            {"email": "boss@occacia.com"},
            {
                "admin_id": generate_prefixed_id("ADM"),
                "password_hash": get_password_hash("SuperSecretPassword123!"),
                "staff_role": "super_admin",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        admin_kash, created = _get_or_create(
            db,
            Admin,
            {"email": "kashmikat@gmail.com"},
            {
                "admin_id": generate_prefixed_id("ADM"),
                "password_hash": get_password_hash("SuperSecretPassword123!"),
                "staff_role": "admin",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        approver_id = admin_kash.id or admin_primary.id

        # ── 2. Test Customer ────────────────────────────────────────────────────────
        customer1, created = _get_or_create(
            db,
            Customer,
            {"email": "customer.test@occacia.com"},
            {
                "customer_id": generate_prefixed_id("CUS"),
                "full_name": "Occacia Test Customer",
                "password_hash": get_password_hash("testpass1"),
                "phone": "+94771111000",
                "locale": "en-LK",
                "address": "Colombo, Sri Lanka",
                "email_verified": True,
                "status": "ACTIVE",
            },
        )
        created_rows += int(created)

        # ── 3. Curated Vendors & Organizations ──────────────────────────────────────
        SHARED_VENDOR_PASSWORD = "Vendor123!"
        PHOTOGRAPHY_VENDOR_PASSWORD = "Abc@123"

        def _create_org_and_vendor(
            *,
            org_name: str,
            org_email: str,
            org_phone: str,
            org_address: str,
            vendor_email: str,
            vendor_name: str,
            display_name: str,
            phone: str,
            location: str,
            password: str,
        ) -> tuple[Organization, Vendor]:
            nonlocal created_rows
            org_lookup = {"email": org_email}
            org, created = _get_or_create(
                db,
                Organization,
                org_lookup,
                {
                    "name": org_name,
                    "legal_name": org_name,
                    "email": org_email,
                    "phone": org_phone,
                    "address": org_address,
                    "status": "approved",
                    "reviewed_by": approver_id,
                    "reviewed_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            created_rows += int(created)

            vendor, created = _get_or_create(
                db,
                Vendor,
                {"email": vendor_email},
                {
                    "vendor_id": generate_prefixed_id("VND"),
                    "business_name": vendor_name,
                    "display_name": display_name,
                    "location_base": location,
                    "phone": phone,
                    "organization_id": org.id,
                    "approval_status": "APPROVED",
                    "approved_at": now,
                    "is_verified": True,
                    "password_hash": get_password_hash(password),
                },
            )
            created_rows += int(created)
            return org, vendor

        def _create_offerings(vendor: Vendor, offerings: list[dict]) -> None:
            nonlocal created_rows
            for item in offerings:
                _, created = _get_or_create(
                    db,
                    Offering,
                    {"vendor_id": vendor.vendor_id, "name": item["name"]},
                    {
                        "offering_id": generate_prefixed_id("OFF"),
                        "category": item["category"],
                        "description": item["description"],
                        "price": float(item["price"]),
                        "currency": "LKR",
                        "unit": item.get("unit", "event"),
                        "quality_tier": item.get("quality_tier", "MEDIUM"),
                        "is_active": True,
                        "is_available": True,
                    },
                )
                created_rows += int(created)

        curated = [
            {
                "category": "cakes & bakery",
                "vendors": [
                    {
                        "org_name": "Cakes by Caramel (Pvt) Ltd",
                        "org_email": "hello@cakesbycaramel.lk",
                        "org_phone": "+94112550011",
                        "org_address": "Union Place, Colombo 02",
                        "vendor_email": "orders@cakesbycaramel.lk",
                        "vendor_name": "Cakes by Caramel",
                        "display_name": "Cakes by Caramel",
                        "phone": "+94771234511",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Custom Celebration Cake",
                                "category": "cakes & bakery",
                                "description": "Bespoke cake design with premium fillings.",
                                "price": 42000,
                                "unit": "cake",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Sweet Oven (Pvt) Ltd",
                        "org_email": "info@kandysweetoven.lk",
                        "org_phone": "+94812222011",
                        "org_address": "Peradeniya Rd, Kandy",
                        "vendor_email": "orders@kandysweetoven.lk",
                        "vendor_name": "Kandy Sweet Oven",
                        "display_name": "Kandy Sweet Oven",
                        "phone": "+94772111222",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Buttercream Party Cake",
                                "category": "cakes & bakery",
                                "description": "Classic buttercream cake for 40-60 guests.",
                                "price": 28000,
                                "unit": "cake",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Galle Gateaux (Pvt) Ltd",
                        "org_email": "hello@gategaux.lk",
                        "org_phone": "+94912222011",
                        "org_address": "Hospital Rd, Galle",
                        "vendor_email": "orders@gategaux.lk",
                        "vendor_name": "Galle Gateaux",
                        "display_name": "Galle Gateaux",
                        "phone": "+94770111233",
                        "location": "Galle",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Fondant Signature Cake",
                                "category": "cakes & bakery",
                                "description": "Elegant fondant cake with handcrafted toppers.",
                                "price": 36000,
                                "unit": "cake",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "catering",
                "vendors": [
                    {
                        "org_name": "Cinnamon Catering (Pvt) Ltd",
                        "org_email": "events@cinnamoncatering.lk",
                        "org_phone": "+94112340055",
                        "org_address": "Duplication Rd, Colombo 03",
                        "vendor_email": "sales@cinnamoncatering.lk",
                        "vendor_name": "Cinnamon Catering",
                        "display_name": "Cinnamon Catering",
                        "phone": "+94771230055",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Premium Buffet Menu",
                                "category": "catering",
                                "description": "Sri Lankan + continental buffet with service staff.",
                                "price": 3200,
                                "unit": "per_head",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Banquet Caterers (Pvt) Ltd",
                        "org_email": "hello@kandybanquet.lk",
                        "org_phone": "+94812223055",
                        "org_address": "Ampitiya Rd, Kandy",
                        "vendor_email": "orders@kandybanquet.lk",
                        "vendor_name": "Kandy Banquet Caterers",
                        "display_name": "Kandy Banquet Caterers",
                        "phone": "+94772123055",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Classic Banquet Menu",
                                "category": "catering",
                                "description": "Traditional menu with dessert station.",
                                "price": 2200,
                                "unit": "per_head",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Southern Feast Catering (Pvt) Ltd",
                        "org_email": "events@southernfeast.lk",
                        "org_phone": "+94412223055",
                        "org_address": "Matara Rd, Matara",
                        "vendor_email": "orders@southernfeast.lk",
                        "vendor_name": "Southern Feast Catering",
                        "display_name": "Southern Feast Catering",
                        "phone": "+94770123055",
                        "location": "Matara",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Seafood & BBQ Spread",
                                "category": "catering",
                                "description": "Southern seafood BBQ with live grilling.",
                                "price": 2600,
                                "unit": "per_head",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "drinks & bar",
                "vendors": [
                    {
                        "org_name": "Lanka Mobile Bar (Pvt) Ltd",
                        "org_email": "book@lankamobilebar.lk",
                        "org_phone": "+94112660110",
                        "org_address": "Nawala Rd, Colombo",
                        "vendor_email": "events@lankamobilebar.lk",
                        "vendor_name": "Lanka Mobile Bar",
                        "display_name": "Lanka Mobile Bar",
                        "phone": "+94771266011",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Mobile Bar Package",
                                "category": "drinks & bar",
                                "description": "Bartenders, glassware, and signature mocktails.",
                                "price": 95000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Colombo Mocktail Lab (Pvt) Ltd",
                        "org_email": "hello@mocktaillab.lk",
                        "org_phone": "+94112660220",
                        "org_address": "Havelock Rd, Colombo",
                        "vendor_email": "events@mocktaillab.lk",
                        "vendor_name": "Colombo Mocktail Lab",
                        "display_name": "Colombo Mocktail Lab",
                        "phone": "+94771266220",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Signature Mocktail Station",
                                "category": "drinks & bar",
                                "description": "Live mocktail bar with 5 signature blends.",
                                "price": 65000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Hill Country Beverage Co (Pvt) Ltd",
                        "org_email": "info@hillcountrybev.lk",
                        "org_phone": "+94812226010",
                        "org_address": "Peradeniya Rd, Kandy",
                        "vendor_email": "events@hillcountrybev.lk",
                        "vendor_name": "Hill Country Beverage Co.",
                        "display_name": "Hill Country Beverage Co.",
                        "phone": "+94772126610",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Tea & Refreshment Bar",
                                "category": "drinks & bar",
                                "description": "Ceylon tea, infusions, and chilled drinks.",
                                "price": 35000,
                                "unit": "event",
                                "quality_tier": "LOW",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "dj & music",
                "vendors": [
                    {
                        "org_name": "DJ Pulse Colombo (Pvt) Ltd",
                        "org_email": "bookings@djpulse.lk",
                        "org_phone": "+94112670033",
                        "org_address": "Union Place, Colombo 02",
                        "vendor_email": "dj@djpulse.lk",
                        "vendor_name": "DJ Pulse Colombo",
                        "display_name": "DJ Pulse Colombo",
                        "phone": "+94771267033",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "DJ Set (4 Hours)",
                                "category": "dj & music",
                                "description": "Professional DJ with full sound setup.",
                                "price": 65000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Night Beats (Pvt) Ltd",
                        "org_email": "hello@kandynightbeats.lk",
                        "org_phone": "+94812227033",
                        "org_address": "Katugastota Rd, Kandy",
                        "vendor_email": "dj@kandynightbeats.lk",
                        "vendor_name": "Kandy Night Beats",
                        "display_name": "Kandy Night Beats",
                        "phone": "+94772127033",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "DJ + MC Package",
                                "category": "dj & music",
                                "description": "DJ performance with event MC hosting.",
                                "price": 48000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Galle Groove DJs (Pvt) Ltd",
                        "org_email": "book@groovedjs.lk",
                        "org_phone": "+94912227033",
                        "org_address": "Lighthouse St, Galle",
                        "vendor_email": "dj@groovedjs.lk",
                        "vendor_name": "Galle Groove DJs",
                        "display_name": "Galle Groove DJs",
                        "phone": "+94770127033",
                        "location": "Galle",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Beach Party DJ Set",
                                "category": "dj & music",
                                "description": "DJ set tailored for coastal events.",
                                "price": 52000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "photography & videography",
                "vendors": [
                    {
                        "org_name": "Tisal Photography (Pvt) Ltd",
                        "org_email": "studio@tisalphoto.lk",
                        "org_phone": "+94112680011",
                        "org_address": "Nugegoda, Colombo",
                        "vendor_email": "tisal.20221672@iit.ac.lk",
                        "vendor_name": "Tisal Photography",
                        "display_name": "Tisal Photography",
                        "phone": "+94771268011",
                        "location": "Colombo",
                        "password": PHOTOGRAPHY_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Basic Photography Package",
                                "category": "photography & videography",
                                "description": "4-hour coverage with 150 edited photos.",
                                "price": 45000,
                                "unit": "event",
                                "quality_tier": "LOW",
                            },
                            {
                                "name": "Standard Photo + Video",
                                "category": "photography & videography",
                                "description": "6-hour coverage with highlight video.",
                                "price": 85000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                            {
                                "name": "Premium Storytelling Suite",
                                "category": "photography & videography",
                                "description": "Full-day coverage, teaser + cinematic film.",
                                "price": 150000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Lanka Lens Studio (Pvt) Ltd",
                        "org_email": "hello@lankalens.lk",
                        "org_phone": "+94112680022",
                        "org_address": "Bambalapitiya, Colombo",
                        "vendor_email": "book@lankalens.lk",
                        "vendor_name": "Lanka Lens Studio",
                        "display_name": "Lanka Lens Studio",
                        "phone": "+94771268022",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Studio Photography Coverage",
                                "category": "photography & videography",
                                "description": "Creative portraits + event highlights.",
                                "price": 60000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Moment Makers LK (Pvt) Ltd",
                        "org_email": "hello@momentmakers.lk",
                        "org_phone": "+94812228022",
                        "org_address": "Dalada Veediya, Kandy",
                        "vendor_email": "book@momentmakers.lk",
                        "vendor_name": "Moment Makers LK",
                        "display_name": "Moment Makers LK",
                        "phone": "+94772128022",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Highlight Film Package",
                                "category": "photography & videography",
                                "description": "Short cinematic highlight film + photos.",
                                "price": 72000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "band & live music",
                "vendors": [
                    {
                        "org_name": "Colombo Jazz Quintet (Pvt) Ltd",
                        "org_email": "bookings@colombojazz.lk",
                        "org_phone": "+94112690055",
                        "org_address": "Colombo 05",
                        "vendor_email": "bookings@colombojazz.lk",
                        "vendor_name": "Colombo Jazz Quintet",
                        "display_name": "Colombo Jazz Quintet",
                        "phone": "+94773334444",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Live Jazz Band (4 Hours)",
                                "category": "band & live music",
                                "description": "Premium 5-piece jazz band performance.",
                                "price": 85000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Acoustic Trio (Pvt) Ltd",
                        "org_email": "hello@kandyacoustic.lk",
                        "org_phone": "+94812229055",
                        "org_address": "Peradeniya Rd, Kandy",
                        "vendor_email": "book@kandyacoustic.lk",
                        "vendor_name": "Kandy Acoustic Trio",
                        "display_name": "Kandy Acoustic Trio",
                        "phone": "+94772129055",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Acoustic Live Set",
                                "category": "band & live music",
                                "description": "2-hour acoustic set for intimate events.",
                                "price": 48000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Southern Sunset Band (Pvt) Ltd",
                        "org_email": "hello@southernsunsetband.lk",
                        "org_phone": "+94912229055",
                        "org_address": "Beach Rd, Galle",
                        "vendor_email": "book@southernsunsetband.lk",
                        "vendor_name": "Southern Sunset Band",
                        "display_name": "Southern Sunset Band",
                        "phone": "+94770129055",
                        "location": "Galle",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Live Band (3 Hours)",
                                "category": "band & live music",
                                "description": "Live band for sunset and dinner sessions.",
                                "price": 62000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "entertainment",
                "vendors": [
                    {
                        "org_name": "Magician Nimal (Pvt) Ltd",
                        "org_email": "hello@magiciannimal.lk",
                        "org_phone": "+94112710011",
                        "org_address": "Kirulapone, Colombo",
                        "vendor_email": "book@magiciannimal.lk",
                        "vendor_name": "Magician Nimal",
                        "display_name": "Magician Nimal",
                        "phone": "+94771271011",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Magic & Illusion Show",
                                "category": "entertainment",
                                "description": "45-minute stage show + close-up magic.",
                                "price": 55000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Fire Show LK (Pvt) Ltd",
                        "org_email": "hello@fireshowlk.lk",
                        "org_phone": "+94112710022",
                        "org_address": "Moratuwa",
                        "vendor_email": "book@fireshowlk.lk",
                        "vendor_name": "Fire Show LK",
                        "display_name": "Fire Show LK",
                        "phone": "+94771271022",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Fire Dance Performance",
                                "category": "entertainment",
                                "description": "High-impact fire show for grand entrances.",
                                "price": 70000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kids Party Fun Crew (Pvt) Ltd",
                        "org_email": "hello@kidsfuncrew.lk",
                        "org_phone": "+94112710033",
                        "org_address": "Negombo",
                        "vendor_email": "book@kidsfuncrew.lk",
                        "vendor_name": "Kids Party Fun Crew",
                        "display_name": "Kids Party Fun Crew",
                        "phone": "+94771271033",
                        "location": "Negombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Kids Entertainment Set",
                                "category": "entertainment",
                                "description": "Balloon art, games, and mascots.",
                                "price": 35000,
                                "unit": "event",
                                "quality_tier": "LOW",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "floral arrangements",
                "vendors": [
                    {
                        "org_name": "Colombo Bloom Studio (Pvt) Ltd",
                        "org_email": "hello@colombobloom.lk",
                        "org_phone": "+94112720011",
                        "org_address": "Flower Rd, Colombo 07",
                        "vendor_email": "orders@colombobloom.lk",
                        "vendor_name": "Colombo Bloom Studio",
                        "display_name": "Colombo Bloom Studio",
                        "phone": "+94771272011",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Premium Floral Set",
                                "category": "floral arrangements",
                                "description": "Stage florals, table centerpieces, entry arch.",
                                "price": 125000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Orchid House (Pvt) Ltd",
                        "org_email": "hello@kandyorchid.lk",
                        "org_phone": "+94812272011",
                        "org_address": "Peradeniya, Kandy",
                        "vendor_email": "orders@kandyorchid.lk",
                        "vendor_name": "Kandy Orchid House",
                        "display_name": "Kandy Orchid House",
                        "phone": "+94772127211",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Orchid Table Styling",
                                "category": "floral arrangements",
                                "description": "Orchid centerpieces with candle accents.",
                                "price": 65000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Galle Garden Florals (Pvt) Ltd",
                        "org_email": "hello@gallegardenflorals.lk",
                        "org_phone": "+94912272011",
                        "org_address": "Galle Fort, Galle",
                        "vendor_email": "orders@gallegardenflorals.lk",
                        "vendor_name": "Galle Garden Florals",
                        "display_name": "Galle Garden Florals",
                        "phone": "+94770127211",
                        "location": "Galle",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Garden Arch & Bouquet",
                                "category": "floral arrangements",
                                "description": "Outdoor arch with tropical blooms.",
                                "price": 85000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "event decoration",
                "vendors": [
                    {
                        "org_name": "Pearl Event Decor (Pvt) Ltd",
                        "org_email": "hello@pearleventdecor.lk",
                        "org_phone": "+94112730011",
                        "org_address": "Park Rd, Colombo 05",
                        "vendor_email": "book@pearleventdecor.lk",
                        "vendor_name": "Pearl Event Decor",
                        "display_name": "Pearl Event Decor",
                        "phone": "+94771273011",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Luxury Event Styling",
                                "category": "event decoration",
                                "description": "Custom theme decor with stage and lighting.",
                                "price": 180000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Ceylon Party Styling (Pvt) Ltd",
                        "org_email": "hello@ceylonpartystyling.lk",
                        "org_phone": "+94112730022",
                        "org_address": "Rajagiriya",
                        "vendor_email": "book@ceylonpartystyling.lk",
                        "vendor_name": "Ceylon Party Styling",
                        "display_name": "Ceylon Party Styling",
                        "phone": "+94771273022",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Classic Theme Decor",
                                "category": "event decoration",
                                "description": "Balloon, backdrop, and table styling.",
                                "price": 95000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Golden Arch Decor (Pvt) Ltd",
                        "org_email": "hello@goldenarchdecor.lk",
                        "org_phone": "+94112730033",
                        "org_address": "Negombo",
                        "vendor_email": "book@goldenarchdecor.lk",
                        "vendor_name": "Golden Arch Decor",
                        "display_name": "Golden Arch Decor",
                        "phone": "+94771273033",
                        "location": "Negombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Outdoor Event Decor",
                                "category": "event decoration",
                                "description": "Canopy, drapes, and stage accents.",
                                "price": 110000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "venue & spaces",
                "vendors": [
                    {
                        "org_name": "Galle Face Hotel (Pvt) Ltd",
                        "org_email": "events@gallefacehotel.lk",
                        "org_phone": "+94112541010",
                        "org_address": "Galle Face, Colombo 03",
                        "vendor_email": "events@gallefacehotel.lk",
                        "vendor_name": "Galle Face Hotel",
                        "display_name": "Galle Face Hotel",
                        "phone": "+94112541010",
                        "location": "Colombo 03",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Grand Ballroom",
                                "category": "venue & spaces",
                                "description": "Historic grand ballroom with premium facilities.",
                                "price": 500000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Mount Lavinia Hotel (Pvt) Ltd",
                        "org_email": "weddings@mountlaviniahotel.lk",
                        "org_phone": "+94112711711",
                        "org_address": "Mount Lavinia",
                        "vendor_email": "weddings@mountlaviniahotel.lk",
                        "vendor_name": "Mount Lavinia Hotel",
                        "display_name": "Mount Lavinia Hotel",
                        "phone": "+94112711711",
                        "location": "Mount Lavinia",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Oceanfront Lawn",
                                "category": "venue & spaces",
                                "description": "Beachfront lawn setup with sunset views.",
                                "price": 380000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "The Wallawwa (Pvt) Ltd",
                        "org_email": "events@wallawwa.lk",
                        "org_phone": "+94112221100",
                        "org_address": "Negombo",
                        "vendor_email": "events@wallawwa.lk",
                        "vendor_name": "The Wallawwa",
                        "display_name": "The Wallawwa",
                        "phone": "+94112221100",
                        "location": "Negombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Heritage Courtyard Venue",
                                "category": "venue & spaces",
                                "description": "Colonial-style courtyard with garden access.",
                                "price": 420000,
                                "unit": "event",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                ],
            },
            {
                "category": "transport",
                "vendors": [
                    {
                        "org_name": "Colombo Limo Service (Pvt) Ltd",
                        "org_email": "hello@colombolimo.lk",
                        "org_phone": "+94112740011",
                        "org_address": "Cotta Rd, Colombo",
                        "vendor_email": "book@colombolimo.lk",
                        "vendor_name": "Colombo Limo Service",
                        "display_name": "Colombo Limo Service",
                        "phone": "+94771274011",
                        "location": "Colombo",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Luxury Sedan Transfer",
                                "category": "transport",
                                "description": "Chauffeured sedan for VIP transfers.",
                                "price": 28000,
                                "unit": "trip",
                                "quality_tier": "HIGH",
                            },
                        ],
                    },
                    {
                        "org_name": "Kandy Vintage Rides (Pvt) Ltd",
                        "org_email": "hello@kandyvintage.lk",
                        "org_phone": "+94812274011",
                        "org_address": "Katugastota, Kandy",
                        "vendor_email": "book@kandyvintage.lk",
                        "vendor_name": "Kandy Vintage Rides",
                        "display_name": "Kandy Vintage Rides",
                        "phone": "+94772127411",
                        "location": "Kandy",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Classic Car Entrance",
                                "category": "transport",
                                "description": "Vintage car arrival for ceremonies.",
                                "price": 35000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                    {
                        "org_name": "Southern Shuttle Co (Pvt) Ltd",
                        "org_email": "hello@southernshuttle.lk",
                        "org_phone": "+94912274011",
                        "org_address": "Matara Rd, Matara",
                        "vendor_email": "book@southernshuttle.lk",
                        "vendor_name": "Southern Shuttle Co.",
                        "display_name": "Southern Shuttle Co.",
                        "phone": "+94770127411",
                        "location": "Matara",
                        "password": SHARED_VENDOR_PASSWORD,
                        "offerings": [
                            {
                                "name": "Guest Shuttle Service",
                                "category": "transport",
                                "description": "30-seat shuttle for guest transfers.",
                                "price": 45000,
                                "unit": "event",
                                "quality_tier": "MEDIUM",
                            },
                        ],
                    },
                ],
            },
        ]

        for group in curated:
            for v in group["vendors"]:
                _, vendor = _create_org_and_vendor(
                    org_name=v["org_name"],
                    org_email=v["org_email"],
                    org_phone=v["org_phone"],
                    org_address=v["org_address"],
                    vendor_email=v["vendor_email"],
                    vendor_name=v["vendor_name"],
                    display_name=v["display_name"],
                    phone=v["phone"],
                    location=v["location"],
                    password=v["password"],
                )
                _create_offerings(vendor, v["offerings"])


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
