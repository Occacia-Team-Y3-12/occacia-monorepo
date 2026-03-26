from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.vendor import Vendor


def _create_vendor() -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="Integration Vendor",
        display_name="Integration Vendor",
        email=f"vendor-int-{uuid4().hex[:8]}@test.com",
        is_verified=True,
        approval_status="APPROVED",
        location_base="Colombo",
        password_hash="hashed",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def test_vendor_offering_crud_integration(client):
    vendor = _create_vendor()
    access = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    client.headers.update({"Authorization": f"Bearer {access}"})

    create = client.post(
        "/api/v1/vendors/offerings",
        json={
            "name": "Premium Catering",
            "category": "Catering",
            "description": "Full service catering",
            "price": 150000,
            "currency": "LKR",
            "qualityTier": "HIGH",
            "isActive": True,
            "isAvailable": True,
        },
    )
    assert create.status_code == 201
    body = create.json()
    offering_id = body["offeringId"]

    listed = client.get("/api/v1/vendors/offerings")
    assert listed.status_code == 200
    assert any(item["offeringId"] == offering_id for item in listed.json()["items"])

    fetched = client.get(f"/api/v1/vendors/offerings/{offering_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Premium Catering"

    updated = client.put(
        f"/api/v1/vendors/offerings/{offering_id}",
        json={"price": 160000, "qualityTier": "MEDIUM"},
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == 160000

    deleted = client.delete(f"/api/v1/vendors/offerings/{offering_id}")
    assert deleted.status_code == 204
