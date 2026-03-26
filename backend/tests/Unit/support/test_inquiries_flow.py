from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.vendor import Vendor


def _create_customer() -> Customer:
    db = SessionLocal()
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        full_name="Inquiry Customer",
        email=f"inq-cust-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("Pass12345!"),
        phone="+94770000000",
        email_verified=True,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()
    return customer


def _create_vendor() -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="Inquiry Vendor",
        display_name="Inquiry Vendor",
        email=f"inq-vendor-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("VendPass123!"),
        is_verified=True,
        approval_status="APPROVED",
        location_base="Colombo",
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.close()
    return vendor


def _create_admin() -> Admin:
    db = SessionLocal()
    admin = Admin(
        admin_id=f"ADM-{uuid4().hex[:16]}",
        email=f"inq-admin-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("AdminPass123!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def test_customer_inquiry_create_and_list(client):
    customer = _create_customer()
    token = create_access_token({"sub": customer.email, "role": "CUSTOMER"})
    created = client.post(
        "/api/v1/customers/inquiries",
        json={"subject": "Help", "message": "Need assistance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201
    listed = client.get(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert len(listed.json().get("items", [])) >= 1


def test_vendor_inquiry_create_and_list(client):
    vendor = _create_vendor()
    token = create_access_token({"sub": vendor.email, "role": "VENDOR"})
    created = client.post(
        "/api/v1/vendors/inquiries",
        json={"subject": "Vendor Help", "message": "Need support"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201
    listed = client.get(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert len(listed.json().get("items", [])) >= 1


def test_admin_inquiry_list(client):
    admin = _create_admin()
    token = create_access_token({"sub": admin.admin_id, "type": "admin", "role": "staff"})
    listed = client.get(
        "/api/v1/admin/inquiries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
