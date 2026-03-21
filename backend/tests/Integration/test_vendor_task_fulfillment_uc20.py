from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.offering import Offering
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor


def _vendor_headers(email: str) -> dict[str, str]:
    token = create_access_token(data={"sub": email, "role": "VENDOR"})
    return {"Authorization": f"Bearer {token}"}


def _create_event(auth_client, title: str = "Vendor Fulfillment Event") -> str:
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


def _confirm_tasks(auth_client, event_id: str) -> None:
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
) -> tuple[Vendor, Offering]:
    vendor = Vendor(
        business_name=display_name,
        display_name=display_name,
        email=f"{display_name.lower().replace(' ', '-')}-{int(price)}@uc20.test",
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
    return vendor, offering


def _seed_offerings() -> dict[str, dict[str, str]]:
    db = SessionLocal()
    try:
        vendors: dict[str, dict[str, str]] = {}
        for display_name, category, name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Budget Flowers", "flowers", "Simple Flowers", "Basic bouquet", 700.0),
        ):
            vendor, _ = _create_vendor_offering(
                db,
                display_name=display_name,
                category=category,
                name=name,
                description=description,
                price=price,
            )
            vendors[category] = {
                "vendorId": vendor.vendor_id,
                "email": vendor.email,
            }
        db.commit()
        return vendors
    finally:
        db.close()


def _generate_confirmed_order(auth_client) -> tuple[dict, dict[str, dict[str, str]]]:
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a cake", vendor_category="cake")
    _create_task(auth_client, event_id, name="Bring flowers", vendor_category="flowers", quantity=2)
    _confirm_tasks(auth_client, event_id)
    vendors = _seed_offerings()

    recommendation_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert recommendation_response.status_code == 200, recommendation_response.text
    package_id = recommendation_response.json()["packages"][1]["packageId"]

    confirm_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert confirm_response.status_code == 200, confirm_response.text
    return confirm_response.json(), vendors


def _request_for_vendor(body: dict, vendor_id: str) -> dict:
    return next(item for item in body["fulfillmentRequests"] if item["vendorId"] == vendor_id)


def test_vendor_list_and_detail_only_return_owned_fulfillment_requests(auth_client):
    body, vendors = _generate_confirmed_order(auth_client)
    cake_vendor = vendors["cake"]
    flowers_vendor = vendors["flowers"]
    own_request = _request_for_vendor(body, cake_vendor["vendorId"])

    list_response = auth_client.get(
        "/api/v1/vendors/fulfillment-requests",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert list_response.status_code == 200, list_response.text
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["fulfillmentRequestId"] == own_request["fulfillmentRequestId"]
    assert items[0]["status"] == "SENT"
    assert items[0]["respondBy"] is not None

    detail_response = auth_client.get(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["vendorId"] == cake_vendor["vendorId"]

    other_vendor_response = auth_client.get(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}",
        headers=_vendor_headers(flowers_vendor["email"]),
    )
    assert other_vendor_response.status_code == 404


def test_vendor_accept_request_then_progress_task_to_done(auth_client):
    body, vendors = _generate_confirmed_order(auth_client)
    cake_vendor = vendors["cake"]
    own_request = _request_for_vendor(body, cake_vendor["vendorId"])

    accept_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}/response",
        json={"decision": "ACCEPT"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert accept_response.status_code == 200, accept_response.text
    accept_body = accept_response.json()
    assert accept_body["fulfillmentRequest"]["status"] == "ACCEPTED"
    assert accept_body["task"]["status"] == "ASSIGNED"

    task_id = accept_body["task"]["taskId"]

    tasks_response = auth_client.get(
        "/api/v1/vendors/tasks",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert tasks_response.status_code == 200, tasks_response.text
    assert [item["taskId"] for item in tasks_response.json()["items"]] == [task_id]

    invalid_transition = auth_client.put(
        f"/api/v1/vendors/tasks/{task_id}",
        json={"status": "DONE"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert invalid_transition.status_code == 409

    in_progress_response = auth_client.put(
        f"/api/v1/vendors/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert in_progress_response.status_code == 200, in_progress_response.text
    assert in_progress_response.json()["status"] == "IN_PROGRESS"

    done_response = auth_client.put(
        f"/api/v1/vendors/tasks/{task_id}",
        json={"status": "DONE"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert done_response.status_code == 200, done_response.text
    assert done_response.json()["status"] == "DONE"

    task_detail_response = auth_client.get(
        f"/api/v1/vendors/tasks/{task_id}",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert task_detail_response.status_code == 200, task_detail_response.text
    assert task_detail_response.json()["status"] == "DONE"


def test_vendor_reject_request_marks_task_rejected(auth_client):
    body, vendors = _generate_confirmed_order(auth_client)
    flowers_vendor = vendors["flowers"]
    own_request = _request_for_vendor(body, flowers_vendor["vendorId"])

    reject_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}/response",
        json={"decision": "REJECT", "responseNote": "Unavailable"},
        headers=_vendor_headers(flowers_vendor["email"]),
    )
    assert reject_response.status_code == 200, reject_response.text
    reject_body = reject_response.json()
    assert reject_body["fulfillmentRequest"]["status"] == "REJECTED"
    assert reject_body["task"]["status"] == "REJECTED"
    assert reject_body["task"]["rejectionReason"] == "Unavailable"

    rejected_list_response = auth_client.get(
        "/api/v1/vendors/tasks",
        params={"status": "REJECTED"},
        headers=_vendor_headers(flowers_vendor["email"]),
    )
    assert rejected_list_response.status_code == 200, rejected_list_response.text
    assert [item["taskId"] for item in rejected_list_response.json()["items"]] == [reject_body["task"]["taskId"]]


def test_vendor_expired_request_is_materialized_on_read_and_cannot_be_accepted(auth_client):
    body, vendors = _generate_confirmed_order(auth_client)
    cake_vendor = vendors["cake"]
    own_request = _request_for_vendor(body, cake_vendor["vendorId"])

    db = SessionLocal()
    try:
        request = (
            db.query(TaskRequest)
            .filter(TaskRequest.request_id == own_request["fulfillmentRequestId"])
            .first()
        )
        assert request is not None
        request.respond_by = request.requested_at
        db.add(request)
        db.commit()
    finally:
        db.close()

    detail_response = auth_client.get(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["status"] == "EXPIRED"

    accept_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{own_request['fulfillmentRequestId']}/response",
        json={"decision": "ACCEPT"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert accept_response.status_code == 409

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == own_request["taskId"]).first()
        assert task is not None
        assert task.status == "EXPIRED"
        assert task.expires_at is not None
    finally:
        db.close()
