from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.vendor import Vendor


def _create_vendor() -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="JIT Vendor",
        display_name="JIT Vendor",
        email=f"jit-vendor-{uuid4().hex[:8]}@test.com",
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


def test_vendor_offering_list_jit(client):
    vendor = _create_vendor()
    access = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    client.headers.update({"Authorization": f"Bearer {access}"})

    response = client.get("/api/v1/vendors/offerings")
    assert response.status_code == 200
    assert "items" in response.json()
