from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.offering import Offering
from app.models.package_execution_request import PackageExecutionRequest
from app.models.package_item import PackageItem
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor


def _create_event(auth_client, title: str = "Confirm Package Event") -> str:
    response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()["eventId"]


def _create_task(auth_client, event_id: str, *, name: str, vendor_category: str, quantity: int = 1) -> str:
    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": name,
            "quantity": quantity,
            "needsVendor": True,
            "vendorCategory": vendor_category,
            "currency": "LKR",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["taskId"]


def _confirm_tasks(auth_client, event_id: str):
    response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert response.status_code == 200, response.text


def _create_vendor_offering(
    db,
    *,
    display_name: str,
    category: str,
    name: str,
    description: str,
    price: float,
) -> Offering:
    vendor = Vendor(
        business_name=display_name,
        display_name=display_name,
        email=f"{display_name.lower().replace(' ', '-')}-{price}@test.com",
        approval_status="APPROVED",
        is_verified=True,
    )
    db.add(vendor)
    db.flush()

    offering = Offering(
        vendor_id=vendor.vendor_id,
        name=name,
        category=category,
        description=description,
        price=price,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.flush()
    return offering


def _seed_offerings():
    db = SessionLocal()
    try:
        for display_name, category, name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Classic Cakes", "cake", "Classic Chocolate Cake", "Chocolate cake", 1400.0),
            ("Budget Flowers", "flowers", "Simple Flowers", "Basic bouquet", 700.0),
            ("Care Flowers", "flowers", "Care Basket", "Flower basket", 1100.0),
        ):
            _create_vendor_offering(
                db,
                display_name=display_name,
                category=category,
                name=name,
                description=description,
                price=price,
            )
        db.commit()
    finally:
        db.close()


def _generate_package(auth_client) -> tuple[str, str]:
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a cake", vendor_category="cake")
    _create_task(auth_client, event_id, name="Bring flowers", vendor_category="flowers", quantity=2)
    _confirm_tasks(auth_client, event_id)
    _seed_offerings()
    response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert response.status_code == 200, response.text
    package_id = response.json()["packages"][1]["packageId"]
    return event_id, package_id


def test_confirm_package_creates_order_updates_tasks_and_creates_fulfillment_requests(auth_client):
    event_id, package_id = _generate_package(auth_client)

    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["packageOrder"]["eventId"] == event_id
    assert body["packageOrder"]["packageId"] == package_id
    assert body["packageOrder"]["status"] == "CREATED"
    assert len(body["tasks"]) == 2
    assert len(body["fulfillmentRequests"]) == 2
    assert all(task["status"] == "PENDING" for task in body["tasks"])
    assert all(task["selectedOfferingId"] for task in body["tasks"])
    assert all(task["assignedVendorId"] for task in body["tasks"])
    assert all(task["lockedAt"] is not None for task in body["tasks"])
    assert all(request["packageOrderId"] == body["packageOrder"]["packageOrderId"] for request in body["fulfillmentRequests"])
    assert all(request["status"] == "SENT" for request in body["fulfillmentRequests"])

    db = SessionLocal()
    try:
        order = (
            db.query(PackageExecutionRequest)
            .filter(PackageExecutionRequest.execution_request_id == body["packageOrder"]["packageOrderId"])
            .first()
        )
        assert order is not None
        assert db.query(TaskRequest).filter(TaskRequest.package_order_id == order.execution_request_id).count() == 2
        tasks = db.query(Task).filter(Task.event_id == event_id).all()
        assert len(tasks) == 2
        assert all(task.locked_at is not None for task in tasks)
    finally:
        db.close()


def test_confirm_package_is_idempotent_for_same_event_and_package(auth_client):
    event_id, package_id = _generate_package(auth_client)

    first = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )
    second = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["packageOrder"]["packageOrderId"] == first.json()["packageOrder"]["packageOrderId"]
    assert len(second.json()["fulfillmentRequests"]) == 2

    db = SessionLocal()
    try:
        assert db.query(PackageExecutionRequest).count() == 1
        assert db.query(TaskRequest).count() == 2
    finally:
        db.close()


def test_confirm_package_fails_when_selected_offering_is_unavailable_and_keeps_state_unchanged(auth_client):
    event_id, package_id = _generate_package(auth_client)

    db = SessionLocal()
    try:
        package_item = (
            db.query(PackageItem)
            .filter(PackageItem.package_id == package_id)
            .order_by(PackageItem.id.asc())
            .first()
        )
        assert package_item is not None
        selected_offering = (
            db.query(Offering)
            .filter(Offering.offering_id == package_item.offering_id)
            .first()
        )
        selected_offering.is_available = False
        db.add(selected_offering)
        db.commit()
    finally:
        db.close()

    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Offering")

    db = SessionLocal()
    try:
        tasks = db.query(Task).filter(Task.event_id == event_id).all()
        assert db.query(PackageExecutionRequest).count() == 0
        assert db.query(TaskRequest).count() == 0
        assert all(task.selected_offering_id is None for task in tasks)
        assert all(task.assigned_vendor_id is None for task in tasks)
        assert all(task.locked_at is None for task in tasks)
    finally:
        db.close()


def test_customer_package_order_list_and_detail_only_return_customer_orders(client, active_customer):
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": active_customer.email, "role": "CUSTOMER"})
    auth_header = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        own_event = Event(
            customer_id=active_customer.customer_id,
            event_type="Family",
            title="Own Event",
            status="ACTIVE",
        )
        other_customer = Customer(
            email=f"other-{uuid4().hex[:8]}@test.com",
            full_name="Other User",
            password_hash="...",
            email_verified=True,
            status="ACTIVE",
            customer_id=f"CUS-{uuid4().hex[:16]}",
        )
        db.add(own_event)
        db.add(other_customer)
        db.flush()

        other_event = Event(
            customer_id=other_customer.customer_id,
            event_type="Family",
            title="Other Event",
            status="ACTIVE",
        )
        db.add(other_event)
        db.flush()

        own_task = Task(
            event_id=own_event.event_id,
            name="Cake",
            quantity=1,
            currency="LKR",
            status="PENDING",
        )
        other_task = Task(
            event_id=other_event.event_id,
            name="Flowers",
            quantity=1,
            currency="LKR",
            status="PENDING",
        )
        db.add(own_task)
        db.add(other_task)
        db.flush()

        own_order = PackageExecutionRequest(
            event_id=own_event.event_id,
            package_id="PKG-OWN",
            idempotency_key=str(uuid4()),
            currency="LKR",
            package_total_price=5000.0,
            status="CREATED",
        )
        other_order = PackageExecutionRequest(
            event_id=other_event.event_id,
            package_id="PKG-OTHER",
            idempotency_key=str(uuid4()),
            currency="LKR",
            package_total_price=7000.0,
            status="CREATED",
        )
        db.add(own_order)
        db.add(other_order)
        db.flush()

        db.add(
            TaskRequest(
                package_order_id=own_order.execution_request_id,
                task_id=own_task.task_id,
                vendor_id="VEN-001",
                offering_id="OFF-001",
                status="SENT",
                attempt_no=1,
            )
        )
        db.add(
            TaskRequest(
                package_order_id=other_order.execution_request_id,
                task_id=other_task.task_id,
                vendor_id="VEN-002",
                offering_id="OFF-002",
                status="SENT",
                attempt_no=1,
            )
        )
        db.commit()
        own_package_order_id = own_order.execution_request_id
        other_package_order_id = other_order.execution_request_id
        own_task_id = own_task.task_id
    finally:
        db.close()

    list_response = client.get("/api/v1/customers/package-orders", headers=auth_header)

    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert len(list_body["items"]) == 1
    assert list_body["items"][0]["packageOrderId"] == own_package_order_id

    detail_response = client.get(
        f"/api/v1/customers/package-orders/{own_package_order_id}",
        headers=auth_header,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail_body = detail_response.json()
    assert detail_body["packageOrder"]["packageOrderId"] == own_package_order_id
    assert [task["taskId"] for task in detail_body["tasks"]] == [own_task_id]

    foreign_detail_response = client.get(
        f"/api/v1/customers/package-orders/{other_package_order_id}",
        headers=auth_header,
    )
    assert foreign_detail_response.status_code == 404
