# ruff: noqa: S101

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.offering import Offering
from app.models.package_execution_request import PackageExecutionRequest
from app.models.support_note import SupportNote
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor


def _admin_headers(admin_id: str) -> dict[str, str]:
    token = create_access_token(data={"sub": admin_id, "type": "admin"})
    return {"Authorization": f"Bearer {token}"}


def test_whenAdminViewsMonitoringDashboardAndPerformsSupportActions_systemReturnsConsistentState(client):
    db = SessionLocal()
    try:
        admin = Admin(
            email=f"admin-{uuid4().hex[:8]}@jit.test",
            password_hash=get_password_hash("AdminPass1!"),
            staff_role="staff",
        )
        customer = Customer(
            customer_id=f"CUS-{uuid4().hex[:16]}",
            email=f"customer-{uuid4().hex[:8]}@jit.test",
            full_name="JIT Customer",
            password_hash=get_password_hash("CustomerPass1!"),
            email_verified=True,
            status="ACTIVE",
        )
        event = Event(
            event_id=f"EVT-{uuid4().hex[:16]}",
            customer_id=customer.customer_id,
            event_type="Family",
            title="JIT Monitoring Event",
            status="ACTIVE",
        )
        vendor_a = Vendor(
            business_name="JIT Cake A",
            display_name="JIT Cake A",
            email=f"a-{uuid4().hex[:8]}@jit.test",
            approval_status="APPROVED",
            is_verified=True,
        )
        vendor_b = Vendor(
            business_name="JIT Cake B",
            display_name="JIT Cake B",
            email=f"b-{uuid4().hex[:8]}@jit.test",
            approval_status="APPROVED",
            is_verified=True,
        )
        db.add_all([admin, customer, event, vendor_a, vendor_b])
        db.flush()

        offering_a = Offering(
            vendor_id=vendor_a.vendor_id,
            name="Cake A Offering",
            category="cake",
            description="Primary vendor",
            price=1000.0,
            currency="LKR",
            is_active=True,
            is_available=True,
        )
        offering_b = Offering(
            vendor_id=vendor_b.vendor_id,
            name="Cake B Offering",
            category="cake",
            description="Replacement vendor",
            price=1200.0,
            currency="LKR",
            is_active=True,
            is_available=True,
        )
        db.add_all([offering_a, offering_b])
        db.flush()

        order = PackageExecutionRequest(
            event_id=event.event_id,
            package_id=f"PKG-{uuid4().hex[:16]}",
            idempotency_key=f"idem-{uuid4().hex}",
            currency="LKR",
            package_total_price=1000.0,
            status="CREATED",
        )
        db.add(order)
        db.flush()

        locked_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        task = Task(
            event_id=event.event_id,
            name="Buy a cake",
            quantity=1,
            currency="LKR",
            needs_vendor="cake",
            status="PENDING",
            selected_offering_id=offering_a.offering_id,
            assigned_vendor_id=vendor_a.vendor_id,
            locked_at=locked_at,
            confirmed_at=locked_at,
            expires_at=locked_at + timedelta(minutes=5),
            status_updated_at=locked_at,
        )
        db.add(task)
        db.flush()
        request = TaskRequest(
            package_order_id=order.execution_request_id,
            task_id=task.task_id,
            vendor_id=vendor_a.vendor_id,
            offering_id=offering_a.offering_id,
            status="SENT",
            requested_at=locked_at,
            respond_by=locked_at + timedelta(minutes=5),
            attempt_no=1,
        )
        db.add(request)
        db.commit()

        admin_id = admin.admin_id
        package_order_id = order.execution_request_id
        task_id = task.task_id
        vendor_b_id = vendor_b.vendor_id
    finally:
        db.close()

    headers = _admin_headers(admin_id)

    orders_response = client.get("/api/v1/admin/package-orders", headers=headers)
    assert orders_response.status_code == 200
    assert orders_response.json()["items"][0]["packageOrderId"] == package_order_id

    tasks_response = client.get("/api/v1/admin/tasks", headers=headers)
    assert tasks_response.status_code == 200
    assert tasks_response.json()["items"][0]["taskId"] == task_id

    detail_response = client.get(f"/api/v1/admin/tasks/{task_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["assignedVendorId"] is not None

    history_response = client.get(f"/api/v1/admin/tasks/{task_id}/fulfillment-requests", headers=headers)
    assert history_response.status_code == 200
    assert len(history_response.json()["items"]) == 1

    note_response = client.post(
        "/api/v1/admin/internal-notes",
        json={
            "packageOrderId": package_order_id,
            "taskId": task_id,
            "actionType": "NOTE_ONLY",
            "note": "Observed delayed response",
        },
        headers=headers,
    )
    assert note_response.status_code == 201

    unlock_response = client.patch(
        f"/api/v1/admin/tasks/{task_id}",
        json={"action": "UNLOCK_EDITING"},
        headers=headers,
    )
    assert unlock_response.status_code == 200
    assert unlock_response.json()["lockedAt"] is None

    reassign_response = client.patch(
        f"/api/v1/admin/tasks/{task_id}",
        json={
            "action": "REASSIGN_VENDOR",
            "assignedVendorId": vendor_b_id,
            "note": "Moved to backup vendor",
        },
        headers=headers,
    )
    assert reassign_response.status_code == 200
    assert reassign_response.json()["assignedVendorId"] == vendor_b_id

    filtered_notes_response = client.get(
        "/api/v1/admin/internal-notes",
        params={"taskId": task_id},
        headers=headers,
    )
    assert filtered_notes_response.status_code == 200
    assert len(filtered_notes_response.json()["items"]) == 2

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        requests = db.query(TaskRequest).filter(TaskRequest.task_id == task_id).order_by(TaskRequest.attempt_no.asc()).all()
        notes = db.query(SupportNote).filter(SupportNote.task_id == task_id).all()
    finally:
        db.close()

    assert task is not None
    assert task.assigned_vendor_id == vendor_b_id
    assert task.locked_at is None
    assert len(requests) == 2
    assert requests[0].status == "CANCELLED"
    assert requests[1].vendor_id == vendor_b_id
    assert len(notes) == 2
