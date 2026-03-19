# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.event import Event
from app.models.package_execution_request import PackageExecutionRequest


def test_whenCustomerTracksEventExecution_listPackageOrders_success(
    auth_client,
    active_customer,
):
    # 1. Create a draft event
    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Birthday", "title": "Birthday Execution Test"},
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

    # 2. Add a task
    task_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={"name": "Catering", "description": "Need food", "quantity": 1},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["taskId"]

    # 3. Confirm tasks to make event ACTIVE
    confirm_tasks_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks/confirm",
        json={"taskIds": [task_id]},
    )
    assert confirm_tasks_response.status_code == 200
    assert confirm_tasks_response.json()["event"]["status"] == "ACTIVE"

    # 4. Manually inject a PackageExecutionRequest (since UC-17 is not yet fully implemented or visible)
    db = SessionLocal()
    try:
        order = PackageExecutionRequest(
            event_id=event_id,
            package_id="PKG-TEST-001",
            idempotency_key="jit-test-key-123",
            currency="LKR",
            package_total_price=15000.0,
            status="PENDING",
            notes="Please handle with care",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        execution_request_id = order.execution_request_id
    finally:
        db.close()

    # 5. Track execution status (UC-18)
    execution_response = auth_client.get(f"/api/v1/customers/events/{event_id}/package-orders")
    
    assert execution_response.status_code == 200
    data = execution_response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    
    order_data = data["items"][0]
    assert order_data["packageOrderId"] == execution_request_id
    assert order_data["eventId"] == event_id
    assert order_data["status"] == "PENDING"
    assert order_data["packageOrderTotalPrice"] == 15000.0
    assert order_data["notes"] == "Please handle with care"
