from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
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


def test_create_package_requires_approved_vendor(client):
    vendor = _create_vendor(approved=False)
    token = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    r = client.post(
        "/api/v1/vendors/me/packages",
        json={
            "name": "Unapproved Package",
            "price": 1200.0,
            "location_coverage": "Colombo",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_create_package_success_for_approved_vendor(client):
    vendor = _create_vendor(approved=True)
    token = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    r = client.post(
        "/api/v1/vendors/me/packages",
        json={
            "name": "Approved Package",
            "price": 2500.0,
            "location_coverage": "Colombo",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Approved Package"
    assert body["price"] == 2500.0


def test_list_packages_requires_auth(client):
    r = client.get("/api/v1/vendors/me/packages")
    assert r.status_code == 401
