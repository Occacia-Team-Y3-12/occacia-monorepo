from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.offering import Offering
from app.models.vendor import Vendor


def _create_vendor(*, approved: bool) -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="Test Vendor",
        display_name="Test Vendor",
        email=f"vendor-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("VendPass123!"),
        is_verified=True,
        approval_status="APPROVED" if approved else "PENDING",
        location_base="Colombo",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def _create_offering(vendor_id: str) -> Offering:
    db = SessionLocal()
    offering = Offering(
        vendor_id=vendor_id,
        name="Photography",
        category="Photography & Videography",
        price=1000.0,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.commit()
    db.refresh(offering)
    db.close()
    return offering


def test_create_offering_requires_auth(client):
    r = client.post("/api/v1/vendors/offerings", json={"name": "X", "category": "Y", "price": 10, "currency": "LKR"})
    assert r.status_code == 401


def test_update_offering_not_owned_returns_404(client):
    vendor_a = _create_vendor(approved=True)
    vendor_b = _create_vendor(approved=True)
    offering = _create_offering(vendor_a.vendor_id)
    token = create_access_token({"sub": vendor_b.email, "role": "VENDOR"})
    r = client.put(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        json={"price": 1200.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


def test_delete_offering_not_owned_returns_404(client):
    vendor_a = _create_vendor(approved=True)
    vendor_b = _create_vendor(approved=True)
    offering = _create_offering(vendor_a.vendor_id)
    token = create_access_token({"sub": vendor_b.email, "role": "VENDOR"})
    r = client.delete(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
