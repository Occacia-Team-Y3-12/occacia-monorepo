from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vendor
from ..schemas import VendorCreate, VendorResponse

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def register_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    # OCA-85: Check for duplicates
    db_vendor = db.query(Vendor).filter(
        (Vendor.email == vendor.email) | (Vendor.business_name == vendor.business_name)
    ).first()
    
    if db_vendor:
        raise HTTPException(status_code=400, detail="Business name or Email already registered")

    # OCA-86 & OCA-87: Create and Save
    new_vendor = Vendor(**vendor.model_dump())
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    # OCA-88/89: Placeholders for Notification logic
    # TODO: Trigger Email background task here
    
    return new_vendor