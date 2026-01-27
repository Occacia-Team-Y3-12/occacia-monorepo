from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.marketplace import Vendor, Package

def seed_data():
    db = SessionLocal()
    
    # Check if data exists
    if db.query(Vendor).first():
        print("⚡ Database already initialized. Skipping seed.")
        db.close()
        return

    print("🌱 Database is empty. Planting seeds...")

    # ==========================================
    # 1. THE INTROVERT (Kandy)
    # ==========================================
    # ✅ FIXED: Using 'business_name', 'email', 'phone' to match your DB
    v1 = Vendor(
        business_name="The Colonial Bungalow", 
        location_base="Kandy", 
        email="stay@colonial.lk", 
        phone="+94771234567",
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

    # ==========================================
    # 2. THE CORPORATE (Colombo)
    # ==========================================
    v2 = Vendor(
        business_name="TechHub Business Center", 
        location_base="Colombo", 
        email="book@techhub.lk", 
        phone="+94112345678",
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

    # ==========================================
    # 3. THE ROMANTIC (Galle)
    # ==========================================
    v3 = Vendor(
        business_name="Cloud9 Rooftop", 
        location_base="Galle", 
        email="love@cloud9.lk", 
        phone="+94779998888",
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

    # ==========================================
    # 4. THE BUDGET PARTY (Colombo)
    # ==========================================
    v4 = Vendor(
        business_name="Burger Shack", 
        location_base="Colombo", 
        email="hey@burgershack.lk", 
        phone="+94775554444",
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

    # ==========================================
    # 5. THE FAMILY (Bentota)
    # ==========================================
    v5 = Vendor(
        business_name="Palm Grove Resort", 
        location_base="Bentota", 
        email="fam@palmgrove.lk", 
        phone="+94342223333",
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

    # ==========================================
    # 6. THE ADVENTURE (Ella)
    # ==========================================
    v6 = Vendor(
        business_name="Wild Trails Camp", 
        location_base="Ella", 
        email="wild@trails.lk", 
        phone="+94711112222",
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
    print("✅ Database Seeded Successfully!")
    db.close()