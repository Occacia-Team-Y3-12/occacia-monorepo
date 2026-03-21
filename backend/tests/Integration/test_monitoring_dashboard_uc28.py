from __future__ import annotations

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


def _customer_headers(email: str) -> dict[str, str]:
    token = create_access_token(data={"sub": email, "role": "CUSTOMER"})
    return {"Authorization": f"Bearer {token}"}


def _create_admin(db, email: str = "admin-uc28@test.com") -> Admin:
    admin = Admin(
        email=email,
        password_hash=get_password_hash("AdminPass1!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _create_customer(db, email: str = "customer-uc28@test.com") -> Customer:
    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:16]}",
        email=email,
        full_name="UC28 Customer",
        password_hash=get_password_hash("CustomerPass1!"),
        email_verified=True,
        status="ACTIVE",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def _create_event_for_customer(db, customer: Customer, title: str) -> Event:
    event = Event(
        event_id=f"EVT-{uuid4().hex[:16]}",
        customer_id=customer.customer_id,
        event_type="Family",
        title=title,
        status="ACTIVE",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _seed_vendor_offering(db, *, name: str, category: str, price: float) -> Vendor:
    vendor = Vendor(
        business_name=name,
        display_name=name,
        email=f"{name.lower().replace(' ', '-')}-{int(price)}@uc28.test",
        approval_status="APPROVED",
        is_verified=True,
    )
    db.add(vendor)
    db.flush()
    offering = Offering(
        vendor_id=vendor.vendor_id,
        name=f"{name} {category}",
        category=category,
        description=f"{category} offering from {name}",
        price=price,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.flush()
    return vendor


def _seed_monitoring_data() -> dict[str, str]:
    db = SessionLocal()
    try:
        admin = _create_admin(db)
        customer = _create_customer(db)
        event = _create_event_for_customer(db, customer, "Monitoring Event")

        primary_vendor = _seed_vendor_offering(db, name="Cake Vendor A", category="cake", price=1000.0)
        secondary_vendor = _seed_vendor_offering(db, name="Cake Vendor B", category="cake", price=1200.0)
        flowers_vendor = _seed_vendor_offering(db, name="Flowers Vendor", category="flowers", price=800.0)

        db.commit()

        cake_offering = db.query(Offering).filter(Offering.vendor_id == primary_vendor.vendor_id).first()
        reassign_offering = db.query(Offering).filter(Offering.vendor_id == secondary_vendor.vendor_id).first()
        flowers_offering = db.query(Offering).filter(Offering.vendor_id == flowers_vendor.vendor_id).first()

        order = PackageExecutionRequest(
            event_id=event.event_id,
            package_id=f"PKG-{uuid4().hex[:16]}",
            idempotency_key=f"idem-{uuid4().hex}",
            currency="LKR",
            package_total_price=1800.0,
            status="CREATED",
        )
        db.add(order)
        db.flush()

        locked_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        cake_task = Task(
            event_id=event.event_id,
            name="Buy a cake",
            quantity=1,
            currency="LKR",
            needs_vendor="cake",
            status="PENDING",
            selected_offering_id=cake_offering.offering_id,
            assigned_vendor_id=primary_vendor.vendor_id,
            locked_at=locked_at,
            confirmed_at=locked_at,
            expires_at=locked_at + timedelta(minutes=5),
            status_updated_at=locked_at,
        )
        flowers_task = Task(
            event_id=event.event_id,
            name="Bring flowers",
            quantity=2,
            currency="LKR",
            needs_vendor="flowers",
            status="ASSIGNED",
            selected_offering_id=flowers_offering.offering_id,
            assigned_vendor_id=flowers_vendor.vendor_id,
            locked_at=locked_at,
            confirmed_at=locked_at,
            status_updated_at=locked_at,
        )
        db.add(cake_task)
        db.add(flowers_task)
        db.flush()

        first_request = TaskRequest(
            package_order_id=order.execution_request_id,
            task_id=cake_task.task_id,
            vendor_id=primary_vendor.vendor_id,
            offering_id=cake_offering.offering_id,
            status="SENT",
            requested_at=locked_at,
            respond_by=locked_at + timedelta(minutes=5),
            attempt_no=1,
        )
        second_request = TaskRequest(
            package_order_id=order.execution_request_id,
            task_id=flowers_task.task_id,
            vendor_id=flowers_vendor.vendor_id,
            offering_id=flowers_offering.offering_id,
            status="ACCEPTED",
            requested_at=locked_at,
            responded_at=locked_at + timedelta(minutes=1),
            attempt_no=1,
        )
        db.add(first_request)
        db.add(second_request)
        db.commit()

        return {
            "adminId": admin.admin_id,
            "customerEmail": customer.email,
            "eventId": event.event_id,
            "packageOrderId": order.execution_request_id,
            "cakeTaskId": cake_task.task_id,
            "flowersTaskId": flowers_task.task_id,
            "primaryVendorId": primary_vendor.vendor_id,
            "secondaryVendorId": secondary_vendor.vendor_id,
            "flowersVendorId": flowers_vendor.vendor_id,
            "reassignOfferingId": reassign_offering.offering_id,
        }
    finally:
        db.close()


def test_internal_note_create_and_list_filters(client):
    data = _seed_monitoring_data()
    headers = _admin_headers(data["adminId"])

    create_response = client.post(
        "/api/v1/admin/internal-notes",
        json={
            "taskId": data["cakeTaskId"],
            "packageOrderId": data["packageOrderId"],
            "actionType": "NOTE_ONLY",
            "note": "Manual review started",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["taskId"] == data["cakeTaskId"]
    assert created["packageOrderId"] == data["packageOrderId"]

    list_response = client.get("/api/v1/admin/internal-notes", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()["items"]) == 1

    by_task_response = client.get(
        "/api/v1/admin/internal-notes",
        params={"taskId": data["cakeTaskId"]},
        headers=headers,
    )
    assert by_task_response.status_code == 200
    assert [item["taskId"] for item in by_task_response.json()["items"]] == [data["cakeTaskId"]]

    by_order_response = client.get(
        "/api/v1/admin/internal-notes",
        params={"packageOrderId": data["packageOrderId"]},
        headers=headers,
    )
    assert by_order_response.status_code == 200
    assert [item["packageOrderId"] for item in by_order_response.json()["items"]] == [data["packageOrderId"]]


def test_package_orders_list_filter_and_detail(client):
    data = _seed_monitoring_data()
    headers = _admin_headers(data["adminId"])

    list_response = client.get("/api/v1/admin/package-orders", headers=headers)
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["packageOrderId"] == data["packageOrderId"]

    filtered_response = client.get(
        "/api/v1/admin/package-orders",
        params={"status": "CREATED"},
        headers=headers,
    )
    assert filtered_response.status_code == 200
    assert [item["status"] for item in filtered_response.json()["items"]] == ["CREATED"]

    detail_response = client.get(
        f"/api/v1/admin/package-orders/{data['packageOrderId']}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["packageOrder"]["packageOrderId"] == data["packageOrderId"]
    assert len(detail["tasks"]) == 2

    not_found_response = client.get("/api/v1/admin/package-orders/EXE-NOTFOUND", headers=headers)
    assert not_found_response.status_code == 404


def test_tasks_list_filters_detail_and_fulfillment_history(client):
    data = _seed_monitoring_data()
    headers = _admin_headers(data["adminId"])

    list_response = client.get("/api/v1/admin/tasks", headers=headers)
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()["items"]) == 2

    by_status_response = client.get(
        "/api/v1/admin/tasks",
        params={"status": "PENDING"},
        headers=headers,
    )
    assert by_status_response.status_code == 200
    assert [item["taskId"] for item in by_status_response.json()["items"]] == [data["cakeTaskId"]]

    by_vendor_response = client.get(
        "/api/v1/admin/tasks",
        params={"vendorId": data["flowersVendorId"]},
        headers=headers,
    )
    assert by_vendor_response.status_code == 200
    assert [item["taskId"] for item in by_vendor_response.json()["items"]] == [data["flowersTaskId"]]

    detail_response = client.get(f"/api/v1/admin/tasks/{data['cakeTaskId']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["taskId"] == data["cakeTaskId"]

    not_found_response = client.get("/api/v1/admin/tasks/TSK-NOTFOUND", headers=headers)
    assert not_found_response.status_code == 404

    history_response = client.get(
        f"/api/v1/admin/tasks/{data['cakeTaskId']}/fulfillment-requests",
        headers=headers,
    )
    assert history_response.status_code == 200
    items = history_response.json()["items"]
    assert len(items) == 1
    assert items[0]["taskId"] == data["cakeTaskId"]
    assert items[0]["packageOrderId"] == data["packageOrderId"]


def test_support_actions_update_db_and_persist_note(client):
    data = _seed_monitoring_data()
    headers = _admin_headers(data["adminId"])
    future_expiry = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    unassign_response = client.patch(
        f"/api/v1/admin/tasks/{data['cakeTaskId']}",
        json={"action": "UNASSIGN_VENDOR"},
        headers=headers,
    )
    assert unassign_response.status_code == 200, unassign_response.text
    assert unassign_response.json()["assignedVendorId"] is None

    extend_response = client.patch(
        f"/api/v1/admin/tasks/{data['cakeTaskId']}",
        json={"action": "EXTEND_EXPIRY", "expiresAt": future_expiry},
        headers=headers,
    )
    assert extend_response.status_code == 200, extend_response.text
    assert extend_response.json()["expiresAt"] is not None

    override_response = client.patch(
        f"/api/v1/admin/tasks/{data['flowersTaskId']}",
        json={"action": "OVERRIDE_STATUS", "status": "IN_PROGRESS"},
        headers=headers,
    )
    assert override_response.status_code == 200, override_response.text
    assert override_response.json()["status"] == "IN_PROGRESS"

    unlock_response = client.patch(
        f"/api/v1/admin/tasks/{data['flowersTaskId']}",
        json={"action": "UNLOCK_EDITING"},
        headers=headers,
    )
    assert unlock_response.status_code == 200, unlock_response.text
    assert unlock_response.json()["lockedAt"] is None

    reassign_response = client.patch(
        f"/api/v1/admin/tasks/{data['cakeTaskId']}",
        json={
            "action": "REASSIGN_VENDOR",
            "assignedVendorId": data["secondaryVendorId"],
            "note": "Escalated and reassigned",
        },
        headers=headers,
    )
    assert reassign_response.status_code == 200, reassign_response.text
    assert reassign_response.json()["assignedVendorId"] == data["secondaryVendorId"]
    assert reassign_response.json()["selectedOfferingId"] is not None

    db = SessionLocal()
    try:
        cake_task = db.query(Task).filter(Task.task_id == data["cakeTaskId"]).first()
        flowers_task = db.query(Task).filter(Task.task_id == data["flowersTaskId"]).first()
        requests = db.query(TaskRequest).filter(TaskRequest.task_id == data["cakeTaskId"]).order_by(TaskRequest.attempt_no.asc()).all()
        notes = db.query(SupportNote).filter(SupportNote.task_id == data["cakeTaskId"]).all()
        assert cake_task is not None
        assert cake_task.assigned_vendor_id == data["secondaryVendorId"]
        assert cake_task.status == "PENDING"
        assert cake_task.expires_at is None
        assert flowers_task is not None
        assert flowers_task.status == "IN_PROGRESS"
        assert flowers_task.locked_at is None
        assert len(requests) == 2
        assert requests[0].status == "CANCELLED"
        assert requests[1].vendor_id == data["secondaryVendorId"]
        assert any(note.action_type == "REASSIGN_VENDOR" and note.note == "Escalated and reassigned" for note in notes)
    finally:
        db.close()


def test_support_action_invalid_payload_and_restricted_action_are_blocked(client):
    data = _seed_monitoring_data()
    headers = _admin_headers(data["adminId"])

    invalid_payload_response = client.patch(
        f"/api/v1/admin/tasks/{data['cakeTaskId']}",
        json={"action": "EXTEND_EXPIRY"},
        headers=headers,
    )
    assert invalid_payload_response.status_code == 400

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == data["flowersTaskId"]).first()
        task.status = "DONE"
        db.add(task)
        db.commit()
    finally:
        db.close()

    restricted_response = client.patch(
        f"/api/v1/admin/tasks/{data['flowersTaskId']}",
        json={"action": "OVERRIDE_STATUS", "status": "ASSIGNED"},
        headers=headers,
    )
    assert restricted_response.status_code == 409


def test_admin_monitoring_auth_rejects_unauthenticated_and_non_admin(client):
    data = _seed_monitoring_data()

    unauthenticated = client.get("/api/v1/admin/tasks")
    assert unauthenticated.status_code == 401

    non_admin = client.get(
        "/api/v1/admin/tasks",
        headers=_customer_headers(data["customerEmail"]),
    )
    assert non_admin.status_code == 401
