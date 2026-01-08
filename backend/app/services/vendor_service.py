from sqlalchemy.orm import Session
from app.models.vendor_model import Vendor
from app.common.security import get_password_hash

# 1. CHECK EMAIL (This was missing!)
def get_vendor_by_email(db: Session, email: str):
    return db.query(Vendor).filter(Vendor.email == email).first()

# 2. CHECK DISPLAY NAME (For unique businesses)
def get_vendor_by_display_name(db: Session, name: str):
    return db.query(Vendor).filter(Vendor.display_name == name).first()

# 3. CREATE VENDOR (The Chef)
def create_vendor(db: Session, vendor_data):
    # Hash the password before it touches the fridge (DB)
    hashed_pwd = get_password_hash(vendor_data.password)
    
    new_vendor = Vendor(
        email=vendor_data.email,
        display_name=vendor_data.display_name,
        phone=vendor_data.phone,
        business_type=vendor_data.business_type,
        address=vendor_data.address,
        hashed_password=hashed_pwd 
    )
    
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor