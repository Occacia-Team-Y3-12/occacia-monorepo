# ruff: noqa: S101

from uuid import uuid4

from app.core.database import SessionLocal
from app.models.offering import Offering
from app.models.package_execution_request import PackageExecutionRequest
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor


def _seed_offering(
    db,
    *,
    vendor_name: str,
    category: str,
    offering_name: str,
    description: str,
    price: float,
):
    vendor = Vendor(
        business_name=vendor_name,
        display_name=vendor_name,
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit-uc17.test",
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


def test_whenCustomerPlacesPackageOrder_confirmListAndGetDetail_success(auth_client):
    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": "Visit Sick Mother"},
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

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
            "quantity": 2,
            "needsVendor": True,
            "vendorCategory": "flowers",
            "currency": "LKR",
        },
    )
    assert flowers_task_response.status_code == 201

    confirm_tasks_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert confirm_tasks_response.status_code == 200
    assert confirm_tasks_response.json()["event"]["status"] == "ACTIVE"

    db = SessionLocal()
    try:
        for vendor_name, category, offering_name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Celebration Cakes", "cake", "Chocolate Celebration Cake", "Chocolate birthday cake", 1500.0),
            ("Luxury Cakes", "cake", "Luxury Designer Cake", "Premium fondant cake", 2600.0),
            ("Budget Flowers", "flowers", "Simple Flowers", "Basic bouquet", 800.0),
            ("Care Flowers", "flowers", "Get Well Flower Basket", "Flower basket", 1200.0),
            ("Luxury Flowers", "flowers", "Grand Orchid Arrangement", "Premium orchids", 2200.0),
        ):
            _seed_offering(
                db,
                vendor_name=vendor_name,
                category=category,
                offering_name=offering_name,
                description=description,
                price=price,
            )
        db.commit()
    finally:
        db.close()

    generate_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert generate_response.status_code == 200
    package_id = generate_response.json()["packages"][1]["packageId"]

    confirm_package_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert confirm_package_response.status_code == 200
    confirm_body = confirm_package_response.json()
    package_order_id = confirm_body["packageOrder"]["packageOrderId"]

    assert confirm_body["packageOrder"]["eventId"] == event_id
    assert confirm_body["packageOrder"]["packageId"] == package_id
    assert confirm_body["packageOrder"]["status"] == "CREATED"
    assert len(confirm_body["tasks"]) == 2
    assert len(confirm_body["fulfillmentRequests"]) == 2
    assert all(task["status"] == "PENDING" for task in confirm_body["tasks"])
    assert all(task["selectedOfferingId"] for task in confirm_body["tasks"])
    assert all(task["assignedVendorId"] for task in confirm_body["tasks"])
    assert all(task["lockedAt"] is not None for task in confirm_body["tasks"])
    assert all(request["packageOrderId"] == package_order_id for request in confirm_body["fulfillmentRequests"])
    assert all(request["status"] == "SENT" for request in confirm_body["fulfillmentRequests"])

    retry_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages/{package_id}/confirm",
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["packageOrder"]["packageOrderId"] == package_order_id

    list_response = auth_client.get("/api/v1/customers/package-orders")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert len(list_body["items"]) == 1
    assert list_body["items"][0]["packageOrderId"] == package_order_id

    detail_response = auth_client.get(f"/api/v1/customers/package-orders/{package_order_id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["packageOrder"]["packageOrderId"] == package_order_id
    assert len(detail_body["tasks"]) == 2

    db = SessionLocal()
    try:
        order = (
            db.query(PackageExecutionRequest)
            .filter(PackageExecutionRequest.execution_request_id == package_order_id)
            .first()
        )
        tasks = db.query(Task).filter(Task.event_id == event_id).all()
        fulfillment_requests = (
            db.query(TaskRequest)
            .filter(TaskRequest.package_order_id == package_order_id)
            .all()
        )
    finally:
        db.close()

    assert order is not None
    assert order.package_id == package_id
    assert len(tasks) == 2
    assert all(task.locked_at is not None for task in tasks)
    assert len(fulfillment_requests) == 2
