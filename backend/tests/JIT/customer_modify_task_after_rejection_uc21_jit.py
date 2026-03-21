# ruff: noqa: S101

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


def _seed_offering(
    db,
    *,
    vendor_name: str,
    category: str,
    offering_name: str,
    description: str,
    price: float,
) -> dict[str, str]:
    vendor = Vendor(
        business_name=vendor_name,
        display_name=vendor_name,
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit-uc21.test",
        approval_status="APPROVED",
        is_verified=True,
    )
    db.add(vendor)
    db.flush()

    offering = Offering(
        vendor_id=vendor.vendor_id,
        name=offering_name,
        category=category,
        description=description,
        price=price,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.flush()

    return {
        "vendorId": vendor.vendor_id,
        "email": vendor.email,
        "offeringId": offering.offering_id,
    }


def _prepare_package_order(auth_client) -> tuple[str, dict, dict[str, list[dict[str, str]]]]:
    create_event_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": "Rejected Task Recovery"},
    )
    assert create_event_response.status_code == 201
    event_id = create_event_response.json()["eventId"]

    flowers_task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": "Bring flowers for mother",
            "description": "Need a florist for the bouquet",
            "quantity": 1,
            "needsVendor": True,
            "vendorCategory": "flowers",
            "currency": "LKR",
        },
    )
    assert flowers_task_response.status_code == 201

    confirm_tasks_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert confirm_tasks_response.status_code == 200

    db = SessionLocal()
    try:
        vendors = {
            "flowers": [
                _seed_offering(
                    db,
                    vendor_name="Budget Flowers",
                    category="flowers",
                    offering_name="Simple Flowers",
                    description="Basic bouquet",
                    price=700.0,
                ),
                _seed_offering(
                    db,
                    vendor_name="Care Flowers",
                    category="flowers",
                    offering_name="Care Basket",
                    description="Flower basket",
                    price=1100.0,
                ),
            ]
        }
        db.commit()
    finally:
        db.close()

    recommendation_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert recommendation_response.status_code == 200
    package_id = recommendation_response.json()["packages"][1]["packageId"]

    confirm_package_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert confirm_package_response.status_code == 200
    return event_id, confirm_package_response.json(), vendors


def _request_for_vendor(fulfillment_requests: list[dict], vendor_id: str) -> dict:
    return next(item for item in fulfillment_requests if item["vendorId"] == vendor_id)


def test_whenCustomerReassignsRejectedTaskOrRemovesIt_systemUpdatesExecutionFlow(auth_client):
    event_id, confirm_body, vendors = _prepare_package_order(auth_client)
    first_vendor = vendors["flowers"][0]
    replacement_vendor = vendors["flowers"][1]
    original_request = _request_for_vendor(confirm_body["fulfillmentRequests"], first_vendor["vendorId"])

    reject_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{original_request['fulfillmentRequestId']}/response",
        json={"decision": "REJECT", "responseNote": "Already booked"},
        headers=_vendor_headers(first_vendor["email"]),
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["task"]["status"] == "REJECTED"

    task_id = reject_response.json()["task"]["taskId"]

    reassign_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/{task_id}/reassign",
        json={"offeringId": replacement_vendor["offeringId"]},
    )
    assert reassign_response.status_code == 200
    assert reassign_response.json()["task"]["status"] == "PENDING"
    assert reassign_response.json()["task"]["assignedVendorId"] == replacement_vendor["vendorId"]
    assert reassign_response.json()["fulfillmentRequest"]["status"] == "SENT"
    assert reassign_response.json()["fulfillmentRequest"]["attemptNo"] == 2

    replacement_inbox_response = auth_client.get(
        "/api/v1/vendors/fulfillment-requests",
        headers=_vendor_headers(replacement_vendor["email"]),
    )
    assert replacement_inbox_response.status_code == 200
    assert replacement_inbox_response.json()["items"][0]["taskId"] == task_id

    second_reject_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{reassign_response.json()['fulfillmentRequest']['fulfillmentRequestId']}/response",
        json={"decision": "REJECT", "responseNote": "Out of stock"},
        headers=_vendor_headers(replacement_vendor["email"]),
    )
    assert second_reject_response.status_code == 200
    assert second_reject_response.json()["task"]["status"] == "REJECTED"

    delete_response = auth_client.delete(f"/api/v1/customers/events/{event_id}/tasks/{task_id}")
    assert delete_response.status_code == 204

    task_list_response = auth_client.get(f"/api/v1/customers/events/{event_id}/tasks")
    assert task_list_response.status_code == 200
    assert task_list_response.json()["items"] == []

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        requests = (
            db.query(TaskRequest)
            .filter(TaskRequest.task_id == task_id)
            .order_by(TaskRequest.attempt_no.asc(), TaskRequest.id.asc())
            .all()
        )
    finally:
        db.close()

    assert task is None
    assert [request.status for request in requests] == ["REJECTED", "REJECTED"]
    assert [request.attempt_no for request in requests] == [1, 2]
