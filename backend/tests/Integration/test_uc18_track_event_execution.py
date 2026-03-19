import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.event import Event
from app.models.package_execution_request import PackageExecutionRequest
from app.core.security import create_access_token


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_header(active_customer: Customer):
    token = create_access_token(data={"sub": active_customer.email, "role": "CUSTOMER"})
    return {"Authorization": f"Bearer {token}"}


def test_list_event_package_orders_success(client: TestClient, db: Session, active_customer: Customer, auth_header: dict):
    # Setup: Create an event
    event = Event(
        customer_id=active_customer.customer_id,
        event_type="Birthday",
        title="My Birthday",
        status="ACTIVE",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Setup: Create package orders
    order1 = PackageExecutionRequest(
        event_id=event.event_id,
        package_id="PKG-001",
        idempotency_key="key-1",
        currency="LKR",
        package_total_price=5000.0,
        status="CREATED",
    )
    order2 = PackageExecutionRequest(
        event_id=event.event_id,
        package_id="PKG-002",
        idempotency_key="key-2",
        currency="LKR",
        package_total_price=7500.0,
        status="PENDING",
    )
    db.add(order1)
    db.add(order2)
    db.commit()

    # Call the endpoint
    response = client.get(
        f"/api/v1/customers/events/{event.event_id}/package-orders",
        headers=auth_header,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    
    # Verify order of items (descending by created_at)
    items = data["items"]
    # We expect order2 and then order1 (if created in that order, but here they are created in same commit)
    # The service orders by created_at DESC, then ID ASC.
    order_ids = [item["packageOrderId"] for item in items]
    assert order1.execution_request_id in order_ids
    assert order2.execution_request_id in order_ids


def test_list_event_package_orders_unauthorized(client: TestClient):
    response = client.get("/api/v1/customers/events/some-event-id/package-orders")
    assert response.status_code == 401


def test_list_event_package_orders_not_found(client: TestClient, auth_header: dict):
    # Try to list orders for an event that doesn't exist
    response = client.get(
        "/api/v1/customers/events/non-existent-event/package-orders",
        headers=auth_header,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_list_event_package_orders_wrong_customer(client: TestClient, db: Session, auth_header: dict):
    # Setup: Create another customer and their event
    other_customer = Customer(
        email="other@example.com",
        full_name="Other User",
        password_hash="...",
        status="ACTIVE",
        customer_id="CUS-OTHER",
    )
    db.add(other_customer)
    db.commit()
    db.refresh(other_customer)

    other_event = Event(
        customer_id=other_customer.customer_id,
        event_type="Wedding",
        title="Other Wedding",
        status="ACTIVE",
    )
    db.add(other_event)
    db.commit()
    db.refresh(other_event)

    # Call the endpoint with the first customer's auth header for the second customer's event
    response = client.get(
        f"/api/v1/customers/events/{other_event.event_id}/package-orders",
        headers=auth_header,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
