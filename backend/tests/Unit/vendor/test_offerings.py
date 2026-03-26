from __future__ import annotations

from uuid import uuid4

from app.common.utils import now_utc
from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.customer import Customer
from app.models.event import Event
from app.models.offering import Offering
from app.models.task import Task
from app.models.task_offering import TaskOffering
from app.models.vendor import Vendor
from app.services.offering_service import offering_service
from app.services.event_planning_service import EventPlanningService, event_planning_service


def _uid() -> str:
    return uuid4().hex[:8]


def _vendor_token(email: str) -> str:
    return create_access_token(data={"sub": email, "role": "VENDOR"})


def _customer_token(email: str) -> str:
    return create_access_token(data={"sub": email, "role": "CUSTOMER"})


def _create_vendor(*, approved: bool) -> Vendor:
    db = SessionLocal()
    try:
        vendor = Vendor(
            vendor_id=f"VEN-{_uid()}",
            business_name=f"Biz-{_uid()}",
            display_name=f"Vendor-{_uid()}",
            email=f"vendor-{_uid()}@test.com",
            password_hash=get_password_hash("Pass12345!"),
            approval_status="APPROVED" if approved else "PENDING",
            is_verified=True,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    finally:
        db.close()


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


def _create_event_and_task(customer: Customer, *, task_name: str = "Birthday Cake", confirmed: bool = False) -> tuple[Event, Task]:
    db = SessionLocal()
    try:
        event = Event(
            event_id=f"EVT-{_uid()}",
            customer_id=customer.customer_id,
            event_type="BIRTHDAY",
            title="Birthday Event",
            status="DRAFT",
        )
        db.add(event)
        db.flush()
        task = Task(
            task_id=f"TSK-{_uid()}",
            event_id=event.event_id,
            name=task_name,
            quantity=1,
            currency="LKR",
            needs_vendor="Cakes & Bakery",
            status="CONFIRMED" if confirmed else "DRAFT",
            confirmed_at=now_utc() if confirmed else None,
        )
        db.add(task)
        db.commit()
        db.query(Event).filter(Event.event_id == event.event_id).update({"status": "ACTIVE"})
        db.commit()
        db.refresh(event)
        db.refresh(task)
        return event, task
    finally:
        db.close()


def _create_offering(vendor: Vendor, *, name: str, category: str = "Cakes & Bakery", price: float = 1000.0) -> Offering:
    db = SessionLocal()
    try:
        offering = Offering(
            vendor_id=vendor.vendor_id,
            name=name,
            category=category,
            description=f"{name} description",
            price=price,
            currency="LKR",
            quality_tier="MEDIUM",
            is_active=True,
            is_available=True,
        )
        db.add(offering)
        db.commit()
        db.refresh(offering)
        return offering
    finally:
        db.close()


def test_infer_category_cake():
    assert offering_service.infer_category("Birthday Cake") == "Cakes & Bakery"


def test_infer_category_dj():
    assert offering_service.infer_category("DJ Set") == "DJ & Music"


def test_infer_category_flowers():
    assert offering_service.infer_category("Flower Arrangement") == "Floral Arrangements"


def test_infer_category_photo():
    assert offering_service.infer_category("Photography Coverage") == "Photography & Videography"


def test_infer_category_catering():
    assert offering_service.infer_category("Food and Catering") == "Catering"


def test_infer_category_venue():
    assert offering_service.infer_category("Venue Booking") == "Venue & Spaces"


def test_infer_category_transport():
    assert offering_service.infer_category("Transport for guests") == "Transport"


def test_infer_category_unknown():
    assert offering_service.infer_category("Random Unknown Thing") == "Other"


def test_vendor_can_create_offering(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    response = client.post(
        "/api/v1/vendors/offerings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Premium Cake",
            "category": "Cakes & Bakery",
            "description": "Chocolate layered cake",
            "price": 15000,
            "currency": "LKR",
            "qualityTier": "HIGH",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["offeringId"]
    assert body["name"] == "Premium Cake"
    assert body["category"] == "Cakes & Bakery"
    assert body["price"] == 15000


def test_create_offering_invalid_category_returns_422(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    response = client.post(
        "/api/v1/vendors/offerings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Weird Item",
            "category": "Not A Real Category",
            "price": 5000,
            "currency": "LKR",
        },
    )
    assert response.status_code == 422


def test_create_offering_negative_price_returns_422(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    response = client.post(
        "/api/v1/vendors/offerings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Negative Price",
            "category": "Cakes & Bakery",
            "price": -1,
            "currency": "LKR",
        },
    )
    assert response.status_code == 422


def test_unapproved_vendor_cannot_create_offering(client):
    vendor = _create_vendor(approved=False)
    token = _vendor_token(vendor.email)
    response = client.post(
        "/api/v1/vendors/offerings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Basic Cake",
            "category": "Cakes & Bakery",
            "price": 5000,
            "currency": "LKR",
        },
    )
    assert response.status_code == 403


def test_unapproved_vendor_cannot_update_offering(client):
    vendor = _create_vendor(approved=True)
    offering = _create_offering(vendor, name="Locked Update", price=1200)
    pending = _create_vendor(approved=False)
    token = _vendor_token(pending.email)
    response = client.put(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": 1900},
    )
    assert response.status_code == 403


def test_unapproved_vendor_cannot_delete_offering(client):
    vendor = _create_vendor(approved=True)
    offering = _create_offering(vendor, name="Locked Delete")
    pending = _create_vendor(approved=False)
    token = _vendor_token(pending.email)
    response = client.delete(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_vendor_can_list_own_offerings(client):
    vendor = _create_vendor(approved=True)
    _create_offering(vendor, name="Cake A")
    _create_offering(vendor, name="Cake B")
    token = _vendor_token(vendor.email)
    response = client.get("/api/v1/vendors/offerings", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def test_vendor_cannot_see_other_vendors_offerings(client):
    owner = _create_vendor(approved=True)
    stranger = _create_vendor(approved=True)
    other_offering = _create_offering(owner, name="Private Offering")
    token = _vendor_token(stranger.email)
    response = client.get(
        f"/api/v1/vendors/offerings/{other_offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (403, 404)


def test_vendor_can_update_own_offering(client):
    vendor = _create_vendor(approved=True)
    offering = _create_offering(vendor, name="Update Me", price=1200)
    token = _vendor_token(vendor.email)
    response = client.put(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": 1800},
    )
    assert response.status_code == 200
    assert response.json()["price"] == 1800


def test_vendor_soft_delete_offering(client):
    vendor = _create_vendor(approved=True)
    offering = _create_offering(vendor, name="Delete Me")
    token = _vendor_token(vendor.email)

    deleted = client.delete(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 204

    db = SessionLocal()
    try:
        row = db.query(Offering).filter(Offering.offering_id == offering.offering_id).first()
        assert row is not None
        assert row.is_active is False
    finally:
        db.close()

    listed = client.get("/api/v1/vendors/offerings", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert all(item["offeringId"] != offering.offering_id for item in listed.json()["items"])


def test_vendor_list_include_inactive_returns_deleted(client):
    vendor = _create_vendor(approved=True)
    offering = _create_offering(vendor, name="Include Me")
    token = _vendor_token(vendor.email)
    client.delete(
        f"/api/v1/vendors/offerings/{offering.offering_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get(
        "/api/v1/vendors/offerings?includeInactive=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    ids = {item["offeringId"] for item in response.json()["items"]}
    assert offering.offering_id in ids


def test_customer_can_browse_task_offerings(client):
    customer = _create_customer()
    vendor = _create_vendor(approved=True)
    event, task = _create_event_and_task(customer, confirmed=False)
    offering = _create_offering(vendor, name="Browse Cake")

    db = SessionLocal()
    try:
        db.add(
            TaskOffering(
                task_id=task.task_id,
                offering_id=offering.offering_id,
                rank=1,
                score=14.5,
                is_selected=False,
            )
        )
        db.commit()
    finally:
        db.close()

    token = _customer_token(customer.email)
    response = client.get(
        f"/api/v1/customers/events/{event.event_id}/tasks/{task.task_id}/offerings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["offeringId"] == offering.offering_id


def test_customer_can_select_offering(client):
    customer = _create_customer()
    vendor = _create_vendor(approved=True)
    event, task = _create_event_and_task(customer, confirmed=False)
    offering_a = _create_offering(vendor, name="Option A")
    offering_b = _create_offering(vendor, name="Option B")

    db = SessionLocal()
    try:
        db.add(TaskOffering(task_id=task.task_id, offering_id=offering_a.offering_id, rank=1, score=15))
        db.add(TaskOffering(task_id=task.task_id, offering_id=offering_b.offering_id, rank=2, score=12))
        db.commit()
    finally:
        db.close()

    token = _customer_token(customer.email)
    response = client.post(
        f"/api/v1/customers/events/{event.event_id}/tasks/{task.task_id}/offerings/{offering_b.offering_id}/select",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["offeringId"] == offering_b.offering_id
    assert response.json()["isSelected"] is True

    db = SessionLocal()
    try:
        task_row = db.query(Task).filter(Task.task_id == task.task_id).first()
        assert task_row is not None
        assert task_row.selected_offering_id == offering_b.offering_id
        assert task_row.assigned_vendor_id == vendor.vendor_id
        selected = (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task.task_id, TaskOffering.offering_id == offering_b.offering_id)
            .first()
        )
        assert selected is not None and selected.is_selected is True
    finally:
        db.close()


def test_customer_select_offering_not_in_shortlist_returns_404(client):
    customer = _create_customer()
    vendor = _create_vendor(approved=True)
    event, task = _create_event_and_task(customer, confirmed=False)
    offering = _create_offering(vendor, name="Outside Shortlist")
    token = _customer_token(customer.email)
    response = client.post(
        f"/api/v1/customers/events/{event.event_id}/tasks/{task.task_id}/offerings/{offering.offering_id}/select",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_get_offering_categories(client):
    response = client.get("/api/v1/offering-categories")
    assert response.status_code == 200
    items = response.json()["items"]
    assert "Cakes & Bakery" in items
    assert "DJ & Music" in items


def test_get_version(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert isinstance(response.json().get("version"), str)
    assert response.json()["version"]


def test_offering_shortlist_created_on_recommendation_generation(client):
    # Some unit tests monkeypatch this singleton method globally; restore real impl.
    event_planning_service.get_event_for_customer = EventPlanningService.get_event_for_customer.__get__(
        event_planning_service,
        EventPlanningService,
    )

    customer = _create_customer()
    vendor = _create_vendor(approved=True)
    _create_offering(vendor, name="Rec Cake A", category="Cakes & Bakery", price=10000)
    _create_offering(vendor, name="Rec Cake B", category="Cakes & Bakery", price=12000)
    event, task = _create_event_and_task(customer, confirmed=True)

    token = _customer_token(customer.email)
    db = SessionLocal()
    try:
        db.query(Event).filter(Event.event_id == event.event_id).update({"status": "ACTIVE"})
        db.query(Task).filter(Task.task_id == task.task_id).update({"confirmed_at": now_utc()})
        db.commit()
    finally:
        db.close()

    generated = client.post(
        f"/api/v1/customers/events/{event.event_id}/recommendations",
        headers={"Authorization": f"Bearer {token}"},
    )
    if generated.status_code == 409:
        db = SessionLocal()
        try:
            db.query(Event).filter(Event.event_id == event.event_id).update({"status": "ACTIVE"})
            db.query(Task).filter(Task.task_id == task.task_id).update({"confirmed_at": now_utc()})
            db.commit()
        finally:
            db.close()
        generated = client.post(
            f"/api/v1/customers/events/{event.event_id}/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert generated.status_code == 200

    shortlist = client.get(
        f"/api/v1/customers/events/{event.event_id}/tasks/{task.task_id}/offerings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert shortlist.status_code == 200
    items = shortlist.json()["items"]
    assert len(items) >= 1
    assert len(items) <= 5
