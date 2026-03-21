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
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit-uc20.test",
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

    return {"vendorId": vendor.vendor_id, "email": vendor.email}


def _prepare_package_order(auth_client) -> tuple[dict, dict[str, dict[str, str]]]:
    create_event_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": "Mother Care Package"},
    )
    assert create_event_response.status_code == 201
    event_id = create_event_response.json()["eventId"]

    cake_task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": "Buy a chocolate cake for mother",
            "description": "Need a thoughtful cake",
            "quantity": 1,
            "needsVendor": True,
            "vendorCategory": "cake",
            "currency": "LKR",
        },
    )
    assert cake_task_response.status_code == 201

    flowers_task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": "Bring flowers for mother",
            "description": "A get well bouquet",
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
            "cake": _seed_offering(
                db,
                vendor_name="Budget Cakes",
                category="cake",
                offering_name="Basic Cake",
                description="Simple vanilla cake",
                price=1000.0,
            ),
            "flowers": _seed_offering(
                db,
                vendor_name="Budget Flowers",
                category="flowers",
                offering_name="Simple Flowers",
                description="Basic bouquet",
                price=700.0,
            ),
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
    return confirm_package_response.json(), vendors


def _request_for_vendor(fulfillment_requests: list[dict], vendor_id: str) -> dict:
    return next(item for item in fulfillment_requests if item["vendorId"] == vendor_id)


def test_whenVendorAcceptsAssignedTask_andMarksProgressToDone_success(auth_client):
    confirm_body, vendors = _prepare_package_order(auth_client)
    cake_vendor = vendors["cake"]
    request = _request_for_vendor(confirm_body["fulfillmentRequests"], cake_vendor["vendorId"])

    inbox_response = auth_client.get(
        "/api/v1/vendors/fulfillment-requests",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert inbox_response.status_code == 200
    assert len(inbox_response.json()["items"]) == 1
    assert inbox_response.json()["items"][0]["status"] == "SENT"
    assert inbox_response.json()["items"][0]["respondBy"] is not None

    accept_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{request['fulfillmentRequestId']}/response",
        json={"decision": "ACCEPT"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert accept_response.status_code == 200
    task_id = accept_response.json()["task"]["taskId"]
    assert accept_response.json()["fulfillmentRequest"]["status"] == "ACCEPTED"
    assert accept_response.json()["task"]["status"] == "ASSIGNED"

    task_list_response = auth_client.get(
        "/api/v1/vendors/tasks",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert task_list_response.status_code == 200
    assert task_list_response.json()["items"][0]["taskId"] == task_id

    in_progress_response = auth_client.put(
        f"/api/v1/vendors/tasks/{task_id}",
        json={"status": "IN_PROGRESS"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert in_progress_response.status_code == 200
    assert in_progress_response.json()["status"] == "IN_PROGRESS"

    done_response = auth_client.put(
        f"/api/v1/vendors/tasks/{task_id}",
        json={"status": "DONE"},
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert done_response.status_code == 200
    assert done_response.json()["status"] == "DONE"

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        fulfillment_request = db.query(TaskRequest).filter(TaskRequest.request_id == request["fulfillmentRequestId"]).first()
    finally:
        db.close()

    assert task is not None
    assert task.status == "DONE"
    assert task.status_updated_at is not None
    assert fulfillment_request is not None
    assert fulfillment_request.status == "ACCEPTED"
    assert fulfillment_request.responded_at is not None


def test_whenVendorRejectsOrMissesAssignedTask_requestBecomesRejectedOrExpired(auth_client):
    confirm_body, vendors = _prepare_package_order(auth_client)
    flowers_vendor = vendors["flowers"]
    cake_vendor = vendors["cake"]
    reject_request = _request_for_vendor(confirm_body["fulfillmentRequests"], flowers_vendor["vendorId"])
    expire_request = _request_for_vendor(confirm_body["fulfillmentRequests"], cake_vendor["vendorId"])

    reject_response = auth_client.post(
        f"/api/v1/vendors/fulfillment-requests/{reject_request['fulfillmentRequestId']}/response",
        json={"decision": "REJECT", "responseNote": "Already booked"},
        headers=_vendor_headers(flowers_vendor["email"]),
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["fulfillmentRequest"]["status"] == "REJECTED"
    assert reject_response.json()["task"]["status"] == "REJECTED"

    db = SessionLocal()
    try:
        pending_request = db.query(TaskRequest).filter(TaskRequest.request_id == expire_request["fulfillmentRequestId"]).first()
        assert pending_request is not None
        pending_request.respond_by = pending_request.requested_at
        db.add(pending_request)
        db.commit()
    finally:
        db.close()

    expired_detail_response = auth_client.get(
        f"/api/v1/vendors/fulfillment-requests/{expire_request['fulfillmentRequestId']}",
        headers=_vendor_headers(cake_vendor["email"]),
    )
    assert expired_detail_response.status_code == 200
    assert expired_detail_response.json()["status"] == "EXPIRED"

    db = SessionLocal()
    try:
        rejected_task = db.query(Task).filter(Task.task_id == reject_request["taskId"]).first()
        expired_task = db.query(Task).filter(Task.task_id == expire_request["taskId"]).first()
        expired_request_row = db.query(TaskRequest).filter(TaskRequest.request_id == expire_request["fulfillmentRequestId"]).first()
    finally:
        db.close()

    assert rejected_task is not None
    assert rejected_task.status == "REJECTED"
    assert rejected_task.rejection_reason == "Already booked"
    assert expired_task is not None
    assert expired_task.status == "EXPIRED"
    assert expired_task.expires_at is not None
    assert expired_request_row is not None
    assert expired_request_row.status == "EXPIRED"
