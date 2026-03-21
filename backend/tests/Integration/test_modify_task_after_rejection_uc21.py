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


def _create_event(auth_client, title: str = "Modify Rejected Task Event") -> str:
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
        email=f"{display_name.lower().replace(' ', '-')}-{int(price)}@uc21.test",
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


def _seed_offerings() -> dict[str, list[dict[str, str]]]:
    db = SessionLocal()
    try:
        vendors: dict[str, list[dict[str, str]]] = {"cake": [], "flowers": []}
        for display_name, category, name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Classic Cakes", "cake", "Classic Chocolate Cake", "Chocolate cake", 1400.0),
            ("Budget Flowers", "flowers", "Simple Flowers", "Basic bouquet", 700.0),
            ("Care Flowers", "flowers", "Care Basket", "Flower basket", 1100.0),
        ):
            vendor, offering = _create_vendor_offering(
                db,
                display_name=display_name,
                category=category,
                name=name,
                description=description,
                price=price,
            )
            vendors[category].append(
                {
                    "vendorId": vendor.vendor_id,
                    "email": vendor.email,
                    "offeringId": offering.offering_id,
                }
            )
        db.commit()
        return vendors
    finally:
        db.close()


def _generate_confirmed_order(auth_client) -> tuple[str, dict, dict[str, list[dict[str, str]]]]:
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
    return event_id, confirm_response.json(), vendors


def _request_for_vendor(body: dict, vendor_id: str) -> dict:
    return next(item for item in body["fulfillmentRequests"] if item["vendorId"] == vendor_id)


def _reject_vendor_request(auth_client, request: dict, vendor_email: str, note: str = "Unavailable") -> dict:
    response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{request['fulfillmentRequestId']}/response",
        json={"decision": "REJECT", "responseNote": note},
        headers=_vendor_headers(vendor_email),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_customer_can_reassign_rejected_task_to_shortlisted_vendor(auth_client):
    event_id, body, vendors = _generate_confirmed_order(auth_client)
    first_flowers_vendor = vendors["flowers"][0]
    replacement_flowers_vendor = vendors["flowers"][1]
    rejected_request = _request_for_vendor(body, first_flowers_vendor["vendorId"])

    rejection = _reject_vendor_request(auth_client, rejected_request, first_flowers_vendor["email"])
    task_id = rejection["task"]["taskId"]

    reassign_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/{task_id}/reassign",
        json={"offeringId": replacement_flowers_vendor["offeringId"], "note": "Try the backup florist"},
    )

    assert reassign_response.status_code == 200, reassign_response.text
    reassign_body = reassign_response.json()
    assert reassign_body["task"]["taskId"] == task_id
    assert reassign_body["task"]["status"] == "PENDING"
    assert reassign_body["task"]["assignedVendorId"] == replacement_flowers_vendor["vendorId"]
    assert reassign_body["task"]["selectedOfferingId"] == replacement_flowers_vendor["offeringId"]
    assert reassign_body["task"]["rejectedAt"] is None
    assert reassign_body["task"]["rejectionReason"] is None
    assert reassign_body["fulfillmentRequest"]["vendorId"] == replacement_flowers_vendor["vendorId"]
    assert reassign_body["fulfillmentRequest"]["offeringId"] == replacement_flowers_vendor["offeringId"]
    assert reassign_body["fulfillmentRequest"]["status"] == "SENT"
    assert reassign_body["fulfillmentRequest"]["attemptNo"] == 2

    list_response = auth_client.get(
        "/api/v1/vendors/fulfillment-requests",
        headers=_vendor_headers(replacement_flowers_vendor["email"]),
    )
    assert list_response.status_code == 200, list_response.text
    assert [item["taskId"] for item in list_response.json()["items"]] == [task_id]

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        requests = (
            db.query(TaskRequest)
            .filter(TaskRequest.task_id == task_id)
            .order_by(TaskRequest.attempt_no.asc(), TaskRequest.id.asc())
            .all()
        )
        assert task is not None
        assert task.status == "PENDING"
        assert task.assigned_vendor_id == replacement_flowers_vendor["vendorId"]
        assert len(requests) == 2
        assert requests[0].status == "REJECTED"
        assert requests[1].status == "SENT"
        assert requests[1].vendor_id == replacement_flowers_vendor["vendorId"]
        assert requests[1].attempt_no == 2
    finally:
        db.close()


def test_customer_reassign_rejected_task_rejects_non_shortlisted_offering(auth_client):
    event_id, body, vendors = _generate_confirmed_order(auth_client)
    first_flowers_vendor = vendors["flowers"][0]
    cake_vendor = vendors["cake"][1]
    rejected_request = _request_for_vendor(body, first_flowers_vendor["vendorId"])
    rejection = _reject_vendor_request(auth_client, rejected_request, first_flowers_vendor["email"])

    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/{rejection['task']['taskId']}/reassign",
        json={"offeringId": cake_vendor["offeringId"]},
    )

    assert response.status_code == 400
    assert "not in the shortlist" in response.json()["detail"]


def test_customer_can_remove_rejected_task_from_event(auth_client):
    event_id, body, vendors = _generate_confirmed_order(auth_client)
    first_flowers_vendor = vendors["flowers"][0]
    rejected_request = _request_for_vendor(body, first_flowers_vendor["vendorId"])
    rejection = _reject_vendor_request(auth_client, rejected_request, first_flowers_vendor["email"])
    task_id = rejection["task"]["taskId"]

    delete_response = auth_client.delete(f"/api/v1/customers/events/{event_id}/tasks/{task_id}")
    assert delete_response.status_code == 204, delete_response.text

    tasks_response = auth_client.get(f"/api/v1/customers/events/{event_id}/tasks")
    assert tasks_response.status_code == 200, tasks_response.text
    assert task_id not in {item["taskId"] for item in tasks_response.json()["items"]}

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        requests = db.query(TaskRequest).filter(TaskRequest.task_id == task_id).count()
        assert task is None
        assert requests == 1
    finally:
        db.close()
