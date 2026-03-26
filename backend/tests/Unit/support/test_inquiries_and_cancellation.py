from __future__ import annotations

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.inquiry import Inquiry
from app.models.package_execution_request import PackageExecutionRequest
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor


def _uid() -> str:
    return uuid4().hex[:8]


def _create_customer() -> Customer:
    db = SessionLocal()
    try:
        customer = Customer(
            customer_id=f"CUS-{_uid()}",
            full_name="Test Customer",
            email=f"customer-{_uid()}@test.com",
            password_hash=get_password_hash("Pass12345!"),
            email_verified=True,
            status="ACTIVE",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    finally:
        db.close()


def _customer_token(email: str) -> str:
    return create_access_token(data={"sub": email})


def _create_vendor() -> Vendor:
    db = SessionLocal()
    try:
        vendor = Vendor(
            vendor_id=f"VEN-{_uid()}",
            business_name=f"Biz-{_uid()}",
            display_name=f"Vendor-{_uid()}",
            email=f"vendor-{_uid()}@test.com",
            password_hash=get_password_hash("Pass12345!"),
            approval_status="APPROVED",
            is_verified=True,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    finally:
        db.close()


def _vendor_token(email: str) -> str:
    return create_access_token(data={"sub": email})


def _create_admin() -> Admin:
    db = SessionLocal()
    try:
        admin = Admin(
            admin_id=f"ADM-{_uid()}",
            email=f"admin-{_uid()}@test.com",
            password_hash=get_password_hash("Pass12345!"),
            staff_role="staff",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    finally:
        db.close()


def _admin_token(admin: Admin) -> str:
    return create_access_token(data={"sub": admin.admin_id, "type": "admin"})


def _create_event_for_customer(customer: Customer) -> Event:
    db = SessionLocal()
    try:
        event = Event(
            event_id=f"EVT-{_uid()}",
            customer_id=customer.customer_id,
            event_type="BIRTHDAY",
            title="Birthday Event",
            status="ACTIVE",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()


def _create_order_with_tasks(
    customer: Customer,
    *,
    order_status: str,
    task_statuses: list[str],
) -> tuple[PackageExecutionRequest, list[Task]]:
    db = SessionLocal()
    try:
        event = Event(
            event_id=f"EVT-{_uid()}",
            customer_id=customer.customer_id,
            event_type="BIRTHDAY",
            title="Birthday Event",
            status="ACTIVE",
        )
        db.add(event)
        db.flush()

        tasks = []
        for idx, status in enumerate(task_statuses, start=1):
            task = Task(
                task_id=f"TSK-{_uid()}-{idx}",
                event_id=event.event_id,
                name=f"Task-{idx}",
                quantity=1,
                currency="LKR",
                status=status,
                assigned_vendor_id=f"VEN-{_uid()}",
                selected_offering_id=f"OFF-{_uid()}",
            )
            db.add(task)
            tasks.append(task)

        order = PackageExecutionRequest(
            execution_request_id=f"EXE-{_uid()}",
            event_id=event.event_id,
            package_id=f"PKG-{_uid()}",
            idempotency_key=f"IDEMP-{_uid()}",
            currency="LKR",
            package_total_price=10000.0,
            status=order_status,
        )
        db.add(order)
        db.flush()

        for task in tasks:
            db.add(
                TaskRequest(
                    request_id=f"TQR-{_uid()}",
                    package_order_id=order.execution_request_id,
                    task_id=task.task_id,
                    vendor_id=task.assigned_vendor_id,
                    offering_id=task.selected_offering_id,
                    status="SENT",
                )
            )

        db.commit()
        db.refresh(order)
        for task in tasks:
            db.refresh(task)
        return order, tasks
    finally:
        db.close()


def test_customer_can_create_inquiry(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    response = client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "Help", "message": "Need assistance"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["inquiryId"]
    assert body["status"] == "OPEN"
    assert body["createdByRole"] == "CUSTOMER"


def test_vendor_can_create_inquiry(client):
    vendor = _create_vendor()
    token = _vendor_token(vendor.email)
    response = client.post(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "Support", "message": "Need help"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["createdByRole"] == "VENDOR"


def test_inquiry_requires_message(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    response = client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "Empty", "message": "   "},
    )
    assert response.status_code == 422


def test_customer_can_list_own_inquiries(client):
    customer = _create_customer()
    other = _create_customer()
    token = _customer_token(customer.email)

    client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "One", "message": "First"},
    )
    client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "Two", "message": "Second"},
    )
    other_token = _customer_token(other.email)
    client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"subject": "Other", "message": "Other"},
    )

    response = client.get(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_customer_can_get_single_inquiry(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    created = client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "One", "message": "First"},
    )
    inquiry_id = created.json()["inquiryId"]
    response = client.get(
        f"/api/v1/customers/inquiries/{inquiry_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["inquiryId"] == inquiry_id


def test_customer_cannot_get_other_users_inquiry(client):
    customer = _create_customer()
    other = _create_customer()
    other_token = _customer_token(other.email)
    created = client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"subject": "Other", "message": "Other"},
    )
    inquiry_id = created.json()["inquiryId"]
    token = _customer_token(customer.email)
    response = client.get(
        f"/api/v1/customers/inquiries/{inquiry_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_vendor_can_list_own_inquiries(client):
    vendor = _create_vendor()
    token = _vendor_token(vendor.email)
    client.post(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "One", "message": "First"},
    )
    client.post(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {token}"},
        json={"subject": "Two", "message": "Second"},
    )
    response = client.get(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_admin_can_list_all_inquiries(client):
    customer = _create_customer()
    vendor = _create_vendor()
    customer_token = _customer_token(customer.email)
    vendor_token = _vendor_token(vendor.email)
    client.post(
        "/api/v1/customers/inquiries",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"subject": "Customer", "message": "Help"},
    )
    client.post(
        "/api/v1/vendors/inquiries",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"subject": "Vendor", "message": "Help"},
    )

    admin = _create_admin()
    admin_token = _admin_token(admin)
    response = client.get(
        "/api/v1/admin/inquiries",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_admin_can_filter_inquiries_by_status(client):
    admin = _create_admin()
    admin_token = _admin_token(admin)
    db = SessionLocal()
    try:
        db.add(
            Inquiry(
                inquiry_id=f"INQ-{_uid()}",
                created_by_user_id="CUS-1",
                created_by_role="CUSTOMER",
                subject="Open",
                message="Open",
                status="OPEN",
            )
        )
        db.add(
            Inquiry(
                inquiry_id=f"INQ-{_uid()}",
                created_by_user_id="VEN-1",
                created_by_role="VENDOR",
                subject="Resolved",
                message="Resolved",
                status="RESOLVED",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/admin/inquiries?status=OPEN",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert all(item["status"] == "OPEN" for item in response.json()["items"])


def test_admin_can_filter_by_creator_role(client):
    admin = _create_admin()
    admin_token = _admin_token(admin)
    db = SessionLocal()
    try:
        db.add(
            Inquiry(
                inquiry_id=f"INQ-{_uid()}",
                created_by_user_id="CUS-1",
                created_by_role="CUSTOMER",
                subject="Customer",
                message="Customer",
                status="OPEN",
            )
        )
        db.add(
            Inquiry(
                inquiry_id=f"INQ-{_uid()}",
                created_by_user_id="VEN-1",
                created_by_role="VENDOR",
                subject="Vendor",
                message="Vendor",
                status="OPEN",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/admin/inquiries?creatorRole=VENDOR",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert all(item["createdByRole"] == "VENDOR" for item in response.json()["items"])


def test_admin_can_reply_and_status_changes_to_in_progress(client):
    admin = _create_admin()
    admin_token = _admin_token(admin)
    db = SessionLocal()
    try:
        inquiry = Inquiry(
            inquiry_id=f"INQ-{_uid()}",
            created_by_user_id="CUS-1",
            created_by_role="CUSTOMER",
            subject="Open",
            message="Open",
            status="OPEN",
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        inquiry_id = inquiry.inquiry_id
    finally:
        db.close()

    response = client.put(
        f"/api/v1/admin/inquiries/{inquiry_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"adminReply": "We are on it"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_admin_can_resolve_inquiry(client):
    admin = _create_admin()
    admin_token = _admin_token(admin)
    db = SessionLocal()
    try:
        inquiry = Inquiry(
            inquiry_id=f"INQ-{_uid()}",
            created_by_user_id="CUS-1",
            created_by_role="CUSTOMER",
            subject="Open",
            message="Open",
            status="OPEN",
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        inquiry_id = inquiry.inquiry_id
    finally:
        db.close()

    response = client.put(
        f"/api/v1/admin/inquiries/{inquiry_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "RESOLVED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"
    assert response.json()["resolvedAt"] is not None


def test_admin_resolve_sets_resolved_at(client):
    admin = _create_admin()
    admin_token = _admin_token(admin)
    db = SessionLocal()
    try:
        inquiry = Inquiry(
            inquiry_id=f"INQ-{_uid()}",
            created_by_user_id="CUS-1",
            created_by_role="CUSTOMER",
            subject="Open",
            message="Open",
            status="OPEN",
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        inquiry_id = inquiry.inquiry_id
    finally:
        db.close()

    response = client.put(
        f"/api/v1/admin/inquiries/{inquiry_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "RESOLVED"},
    )
    assert response.status_code == 200
    assert response.json()["resolvedAt"] is not None


def test_customer_can_cancel_created_order(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    order, tasks = _create_order_with_tasks(
        customer,
        order_status="CREATED",
        task_statuses=["PENDING", "ASSIGNED"],
    )
    response = client.put(
        f"/api/v1/customers/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["packageOrder"]["status"] == "CANCELLED_ADMIN"

    db = SessionLocal()
    try:
        updated_tasks = db.query(Task).filter(Task.event_id == order.event_id).all()
        assert all(task.status == "DRAFT" for task in updated_tasks)
        assert all(task.assigned_vendor_id is None for task in updated_tasks)
        assert all(task.selected_offering_id is None for task in updated_tasks)
        requests = db.query(TaskRequest).filter(TaskRequest.package_order_id == order.execution_request_id).all()
        assert all(req.status == "EXPIRED" for req in requests)
    finally:
        db.close()


def test_customer_cannot_cancel_non_created_order(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    order, _ = _create_order_with_tasks(
        customer,
        order_status="COMPLETED",
        task_statuses=["PENDING"],
    )
    response = client.put(
        f"/api/v1/customers/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


def test_customer_cannot_cancel_other_customers_order(client):
    customer = _create_customer()
    other = _create_customer()
    order, _ = _create_order_with_tasks(
        other,
        order_status="CREATED",
        task_statuses=["PENDING"],
    )
    token = _customer_token(customer.email)
    response = client.put(
        f"/api/v1/customers/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (403, 404)


def test_admin_can_cancel_any_non_completed_order(client):
    customer = _create_customer()
    order, _ = _create_order_with_tasks(
        customer,
        order_status="CREATED",
        task_statuses=["PENDING"],
    )
    admin = _create_admin()
    admin_token = _admin_token(admin)
    response = client.put(
        f"/api/v1/admin/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["packageOrder"]["status"] == "CANCELLED_ADMIN"


def test_admin_cannot_cancel_completed_order(client):
    customer = _create_customer()
    order, _ = _create_order_with_tasks(
        customer,
        order_status="COMPLETED",
        task_statuses=["PENDING"],
    )
    admin = _create_admin()
    admin_token = _admin_token(admin)
    response = client.put(
        f"/api/v1/admin/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


def test_pending_tasks_reverted_to_draft_on_cancel(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    order, _ = _create_order_with_tasks(
        customer,
        order_status="CREATED",
        task_statuses=["PENDING"],
    )
    response = client.put(
        f"/api/v1/customers/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.event_id == order.event_id).first()
        assert task is not None
        assert task.status == "DRAFT"
    finally:
        db.close()


def test_assigned_tasks_reverted_to_draft_on_cancel(client):
    customer = _create_customer()
    token = _customer_token(customer.email)
    order, _ = _create_order_with_tasks(
        customer,
        order_status="CREATED",
        task_statuses=["ASSIGNED"],
    )
    response = client.put(
        f"/api/v1/customers/package-orders/{order.execution_request_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.event_id == order.event_id).first()
        assert task is not None
        assert task.status == "DRAFT"
    finally:
        db.close()
