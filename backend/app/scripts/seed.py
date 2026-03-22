import logging

from sqlalchemy import inspect

from app.common.utils import now_utc
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.vendor import Vendor

logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()

    try:
        inspector = inspect(db.bind)
        required_tables = (Vendor.__tablename__, Package.__tablename__)
        missing_tables = [table for table in required_tables if not inspector.has_table(table)]
        if missing_tables:
            logger.warning(
                "Skipping seed because required tables are missing: %s. "
                "Run `poetry run alembic upgrade heads` first.",
                ", ".join(sorted(missing_tables)),
            )
            return False

        # Check if database is already populated
        if db.query(Vendor).first():
            logger.info("Database already initialized. Skipping seed.")
            return False

        logger.info("Database is empty. Seeding initial data...")

        # --- Vendor 1: Kandy (Introvert/Private) ---
        v1 = Vendor(
            business_name="The Colonial Bungalow",
            display_name="The Colonial Bungalow",
            location_base="Kandy",
            email="stay@colonial.lk",
            phone="+94771234567",
            contact_phone="+94771234567",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v1)
        db.commit()

        db.add(Package(
            vendor_id=v1.id,
            name="The Hermit's Dinner",
            description="A completely private dining experience in a secluded garden booth.",
            price=3500.0,
            min_guests=1,
            max_guests=4,
            location_coverage="Kandy",
            tags=["private-dining", "quiet", "secluded"]
        ))

        # --- Vendor 2: Colombo (Corporate) ---
        v2 = Vendor(
            business_name="TechHub Business Center",
            display_name="TechHub Business Center",
            location_base="Colombo",
            email="book@techhub.lk",
            phone="+94112345678",
            contact_phone="+94112345678",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v2)
        db.commit()

        db.add(Package(
            vendor_id=v2.id,
            name="Executive Boardroom",
            description="Soundproof boardroom with 5G Wifi and 4K Projector.",
            price=5000.0,
            min_guests=5,
            max_guests=20,
            location_coverage="Colombo",
            tags=["projector", "wifi", "business"]
        ))

        # --- Vendor 3: Galle (Romantic) ---
        v3 = Vendor(
            business_name="Cloud9 Rooftop",
            display_name="Cloud9 Rooftop",
            location_base="Galle",
            email="love@cloud9.lk",
            phone="+94779998888",
            contact_phone="+94779998888",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v3)
        db.commit()

        db.add(Package(
            vendor_id=v3.id,
            name="Sunset Proposal Package",
            description="Private rooftop corner with rose petals and candles.",
            price=15000.0,
            min_guests=2,
            max_guests=2,
            location_coverage="Galle",
            tags=["romantic", "proposal", "luxury"]
        ))

        # --- Vendor 4: Colombo (Budget/Party) ---
        v4 = Vendor(
            business_name="Burger Shack",
            display_name="Burger Shack",
            location_base="Colombo",
            email="hey@burgershack.lk",
            phone="+94775554444",
            contact_phone="+94775554444",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v4)
        db.commit()

        db.add(Package(
            vendor_id=v4.id,
            name="Student Birthday Bash",
            description="Reserved large table, loud music, and budget platters.",
            price=1500.0,
            min_guests=10,
            max_guests=30,
            location_coverage="Colombo",
            tags=["budget", "party", "loud"]
        ))

        # --- Vendor 5: Bentota (Family) ---
        v5 = Vendor(
            business_name="Palm Grove Resort",
            display_name="Palm Grove Resort",
            location_base="Bentota",
            email="fam@palmgrove.lk",
            phone="+94342223333",
            contact_phone="+94342223333",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v5)
        db.commit()

        db.add(Package(
            vendor_id=v5.id,
            name="Family Day Out",
            description="Access to kids' pool, buffet lunch, and garden.",
            price=4000.0,
            min_guests=4,
            max_guests=15,
            location_coverage="Bentota",
            tags=["family", "pool", "kids"]
        ))

        # --- Vendor 6: Ella (Adventure) ---
        v6 = Vendor(
            business_name="Wild Trails Camp",
            display_name="Wild Trails Camp",
            location_base="Ella",
            email="wild@trails.lk",
            phone="+94711112222",
            contact_phone="+94711112222",
            approval_status="APPROVED",
            approved_at=now_utc(),
            is_verified=True
        )
        db.add(v6)
        db.commit()

        db.add(Package(
            vendor_id=v6.id,
            name="Jungle BBQ Night",
            description="Camping under the stars with a bonfire BBQ.",
            price=2500.0,
            min_guests=2,
            max_guests=10,
            location_coverage="Ella",
            tags=["nature", "adventure", "camping"]
        ))

        db.commit()
        logger.info("Database seeded successfully.")
        return True
    finally:
        db.close()
