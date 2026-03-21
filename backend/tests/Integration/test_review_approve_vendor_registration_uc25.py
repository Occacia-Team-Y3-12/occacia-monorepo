# ruff: noqa: S101

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.admin import Admin
from app.models.vendor import Vendor
from app.core.security import get_password_hash


def _create_admin(db, email: str = None) -> Admin:
    if email is None:
        email = f"admin-{uuid4().hex[:8]}@test.com"
    admin = Admin(
        email=email,
        password_hash=get_password_hash("Admin1234!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _create_pending_vendor(db, business_name: str = None) -> Vendor:
    if business_name is None:
        business_name = f"Vendor-{uuid4().hex[:6]}"
    vendor = Vendor(
        business_name=business_name,
        display_name=business_name,
        email=f"{business_name.lower().replace(' ', '-')}@test.com",
        approval_status="PENDING",
        is_verified=False,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def test_admin_can_list_pending_vendors(client):
    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        _create_pending_vendor(db, "Pending Vendor 1")
        _create_pending_vendor(db, "Pending Vendor 2")
        approved_vendor = _create_pending_vendor(db, "Approved Vendor")
        approved_vendor.approval_status = "APPROVED"
        db.add(approved_vendor)
        db.commit()
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.get(
        "/api/v1/admin/vendors?approval_status=PENDING",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    assert all(v["approval_status"] == "PENDING" for v in body)


def test_admin_can_get_vendor_detail(client):
    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        vendor = _create_pending_vendor(db, "Test Vendor Detail")
        vendor_id = vendor.id
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.get(
        f"/api/v1/admin/vendors/{vendor_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == vendor_id
    assert body["business_name"] == "Test Vendor Detail"
    assert body["approval_status"] == "PENDING"


def test_admin_can_approve_pending_vendor(client, monkeypatch):
    monkeypatch.setattr("app.routers.v1.admin_router._send_approval_email", lambda v: None)

    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        vendor = _create_pending_vendor(db, "Vendor To Approve")
        vendor_id = vendor.id
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.post(
        f"/api/v1/admin/vendors/{vendor_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["approval_status"] == "APPROVED"
    assert body["is_verified"] is True
    assert body["approved_at"] is not None

    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        assert vendor.approval_status == "APPROVED"
        assert vendor.is_verified is True
        assert vendor.approved_at is not None
    finally:
        db.close()


def test_admin_can_reject_pending_vendor(client, monkeypatch):
    monkeypatch.setattr("app.routers.v1.admin_router._send_rejection_email", lambda v, r: None)

    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        vendor = _create_pending_vendor(db, "Vendor To Reject")
        vendor_id = vendor.id
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.post(
        f"/api/v1/admin/vendors/{vendor_id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Incomplete documentation"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["approval_status"] == "REJECTED"
    assert body["is_verified"] is False

    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        assert vendor.approval_status == "REJECTED"
        assert vendor.is_verified is False
    finally:
        db.close()


def test_approve_already_approved_vendor_fails(client, monkeypatch):
    monkeypatch.setattr("app.routers.v1.admin_router._send_approval_email", lambda v: None)

    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        vendor = _create_pending_vendor(db, "Already Approved")
        vendor.approval_status = "APPROVED"
        vendor.is_verified = True
        db.add(vendor)
        db.commit()
        vendor_id = vendor.id
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.post(
        f"/api/v1/admin/vendors/{vendor_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "already approved" in response.json()["detail"]


def test_reject_already_rejected_vendor_fails(client, monkeypatch):
    monkeypatch.setattr("app.routers.v1.admin_router._send_rejection_email", lambda v, r: None)

    db = SessionLocal()
    try:
        admin = _create_admin(db)
        admin_id = admin.admin_id
        vendor = _create_pending_vendor(db, "Already Rejected")
        vendor.approval_status = "REJECTED"
        vendor.is_verified = False
        db.add(vendor)
        db.commit()
        vendor_id = vendor.id
    finally:
        db.close()

    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    response = client.post(
        f"/api/v1/admin/vendors/{vendor_id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Test"},
    )

    assert response.status_code == 400
    assert "already rejected" in response.json()["detail"]


def test_get_unknown_vendor_returns_404(client):
    db = SessionLocal()
    try:
        admin = _create_admin(db)
    finally:
        db.close()

    token = create_access_token(data={"sub": admin.admin_id, "type": "admin"})
    response = client.get(
        "/api/v1/admin/vendors/999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_approve_unknown_vendor_returns_404(client, monkeypatch):
    monkeypatch.setattr("app.routers.v1.admin_router._send_approval_email", lambda v: None)

    db = SessionLocal()
    try:
        admin = _create_admin(db)
    finally:
        db.close()

    token = create_access_token(data={"sub": admin.admin_id, "type": "admin"})
    response = client.post(
        "/api/v1/admin/vendors/999999/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_non_admin_cannot_list_vendors(client, active_customer):
    token = create_access_token(data={"sub": active_customer.email})
    response = client.get(
        "/api/v1/admin/vendors",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_non_admin_cannot_approve_vendor(client, active_customer):
    token = create_access_token(data={"sub": active_customer.email})
    response = client.post(
        "/api/v1/admin/vendors/1/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_non_admin_cannot_reject_vendor(client, active_customer):
    token = create_access_token(data={"sub": active_customer.email})
    response = client.post(
        "/api/v1/admin/vendors/1/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Test"},
    )

    assert response.status_code == 401
