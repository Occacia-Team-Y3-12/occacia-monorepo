# ruff: noqa: S101

from datetime import timedelta
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.package_execution_request import PackageExecutionRequest
from app.models.user import User
from app.models.vendor import Vendor
from sqlalchemy import text


def _admin_headers(admin_id: str) -> dict[str, str]:
    token = create_access_token(data={"sub": admin_id, "type": "admin"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


def _customer_headers(email: str) -> dict[str, str]:
    token = create_access_token(data={"sub": email, "role": "CUSTOMER"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


def _seed_dashboard_data() -> tuple[str, str]:
    db = SessionLocal()
    try:
        admin = Admin(
            email=f"admin-{uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("AdminPass1!"),
            staff_role="staff",
        )
        customer = Customer(
            customer_id=f"CUS-{uuid4().hex[:16]}",
            email=f"customer-{uuid4().hex[:8]}@test.com",
            full_name="Customer Test",
            password_hash=get_password_hash("CustomerPass1!"),
            email_verified=True,
            status="ACTIVE",
        )

        db.add_all([admin, customer])
        db.flush()

        db.add_all(
            [
                User(
                    user_id=f"USR-{uuid4().hex[:8]}",
                    email=f"user-active-{uuid4().hex[:8]}@test.com",
                    password_hash="x",
                    role="CUSTOMER",
                    status="ACTIVE",
                ),
                User(
                    user_id=f"USR-{uuid4().hex[:8]}",
                    email=f"user-pending-{uuid4().hex[:8]}@test.com",
                    password_hash="x",
                    role="VENDOR",
                    status="PENDING",
                ),
                User(
                    user_id=f"USR-{uuid4().hex[:8]}",
                    email=f"user-disabled-{uuid4().hex[:8]}@test.com",
                    password_hash="x",
                    role="CUSTOMER",
                    status="DISABLED",
                ),
            ]
        )

        db.add_all(
            [
                Vendor(
                    business_name="Vendor Approved",
                    display_name="Vendor Approved",
                    email=f"vendor-a-{uuid4().hex[:8]}@test.com",
                    approval_status="APPROVED",
                    is_verified=True,
                ),
                Vendor(
                    business_name="Vendor Pending",
                    display_name="Vendor Pending",
                    email=f"vendor-p-{uuid4().hex[:8]}@test.com",
                    approval_status="PENDING",
                    is_verified=False,
                ),
            ]
        )

        db.add_all(
            [
                Event(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    customer_id=customer.customer_id,
                    event_type="Family",
                    title="Active Event",
                    status="ACTIVE",
                ),
                Event(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    customer_id=customer.customer_id,
                    event_type="Family",
                    title="Pending Event",
                    status="PENDING",
                ),
                Event(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    customer_id=customer.customer_id,
                    event_type="Family",
                    title="Draft Event",
                    status="DRAFT",
                ),
            ]
        )

        db.add_all(
            [
                PackageExecutionRequest(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    package_id=f"PKG-{uuid4().hex[:16]}",
                    idempotency_key=f"idem-{uuid4().hex}",
                    currency="LKR",
                    package_total_price=1200.0,
                    status="COMPLETED",
                ),
                PackageExecutionRequest(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    package_id=f"PKG-{uuid4().hex[:16]}",
                    idempotency_key=f"idem-{uuid4().hex}",
                    currency="LKR",
                    package_total_price=900.0,
                    status="CREATED",
                ),
                PackageExecutionRequest(
                    event_id=f"EVT-{uuid4().hex[:16]}",
                    package_id=f"PKG-{uuid4().hex[:16]}",
                    idempotency_key=f"idem-{uuid4().hex}",
                    currency="LKR",
                    package_total_price=500.0,
                    status="CANCELLED_ADMIN",
                ),
            ]
        )

        db.commit()
        return admin.admin_id, customer.email
    finally:
        db.close()


def test_admin_dashboard_returns_aggregated_metrics(client):
    admin_id, _ = _seed_dashboard_data()

    response = client.get("/api/v1/admin/dashboard", headers=_admin_headers(admin_id))
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["users"] == {"total": 7, "active": 4, "pending": 2}
    assert payload["usersTable"] == {"total": 3, "active": 1, "pending": 1}
    assert payload["vendors"] == {"total": 2, "active": 1, "pending": 1}
    assert payload["events"] == {"total": 3, "active": 1, "pending": 1}
    assert payload["packageOrders"] == {"total": 3, "active": 1, "pending": 1}
    assert payload["generatedAt"]


def test_admin_dashboard_rejects_unauthenticated_and_non_admin(client):
    admin_id, customer_email = _seed_dashboard_data()
    _ = admin_id

    unauthenticated = client.get("/api/v1/admin/dashboard")
    assert unauthenticated.status_code == 401

    non_admin = client.get("/api/v1/admin/dashboard", headers=_customer_headers(customer_email))
    assert non_admin.status_code == 401


def test_dashboard_count_queries_use_status_indexes():
    db = SessionLocal()
    try:
        plans = {
            "users": db.execute(
                text("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM users WHERE status = 'ACTIVE'")
            ).fetchall(),
            "vendors": db.execute(
                text("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM vendors WHERE approval_status = 'PENDING'")
            ).fetchall(),
            "events": db.execute(
                text("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM events WHERE status = 'ACTIVE'")
            ).fetchall(),
            "package_execution_requests": db.execute(
                text("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM package_execution_requests WHERE status = 'CREATED'")
            ).fetchall(),
        }
    finally:
        db.close()

    assert any("ix_users_status" in str(row) for row in plans["users"])
    assert any("ix_vendors_approval_status" in str(row) for row in plans["vendors"])
    assert any("ix_events_status" in str(row) for row in plans["events"])
    assert any("ix_package_execution_requests_status" in str(row) for row in plans["package_execution_requests"])
