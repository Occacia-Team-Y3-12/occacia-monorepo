from __future__ import annotations

from app.core.database import SessionLocal
from app.models.offering import Offering
from app.models.vendor import Vendor


def _create_event(auth_client, title: str = "Visit Mother") -> str:
    response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()["eventId"]


def _create_task(
    auth_client,
    event_id: str,
    *,
    name: str,
    vendor_category: str,
    quantity: int = 1,
):
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
    currency: str = "LKR",
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
        currency=currency,
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.flush()
    return offering


def _seed_recommendation_offerings():
    db = SessionLocal()
    try:
        _create_vendor_offering(
            db,
            display_name="Budget Cakes",
            category="cake",
            name="Basic Cake",
            description="Simple vanilla cake",
            price=1000.0,
        )
        _create_vendor_offering(
            db,
            display_name="Budget Flowers",
            category="flowers",
            name="Simple Flowers",
            description="Basic bouquet",
            price=800.0,
        )
        db.commit()
    finally:
        db.close()


def test_get_package_details_success(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a cake", vendor_category="cake")
    _create_task(auth_client, event_id, name="Bring flowers", vendor_category="flowers", quantity=2)
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()

    # Generate packages
    gen_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert gen_response.status_code == 200
    packages = gen_response.json()["packages"]
    package_id = packages[0]["packageId"]

    # Get package details
    response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["packageId"] == package_id
    assert body["eventId"] == event_id
    assert "items" in body
    assert len(body["items"]) == 2
    
    # Verify item details
    item = body["items"][0]
    assert "taskId" in item
    assert "taskName" in item
    assert "offeringId" in item
    assert "offeringName" in item
    assert "offeringCategory" in item
    assert "vendorId" in item
    assert "vendorName" in item
    assert "unitPrice" in item
    assert "taskPrice" in item
    assert "currency" in item

    # Specific check for offeringCategory added in this task
    assert item["offeringCategory"] in ["cake", "flowers"]


def test_get_package_details_not_found(auth_client):
    event_id = _create_event(auth_client)
    response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/PKG-INVALID")
    assert response.status_code == 404


def test_get_package_details_wrong_event(auth_client):
    event_id_1 = _create_event(auth_client, title="Event 1")
    event_id_2 = _create_event(auth_client, title="Event 2")
    
    _create_task(auth_client, event_id_1, name="Buy a cake", vendor_category="cake")
    _confirm_tasks(auth_client, event_id_1)
    _seed_recommendation_offerings()

    gen_response = auth_client.post(f"/api/v1/customers/events/{event_id_1}/recommendations")
    package_id = gen_response.json()["packages"][0]["packageId"]

    # Try to access package of event 1 using event 2 ID
    response = auth_client.get(f"/api/v1/customers/events/{event_id_2}/packages/{package_id}")
    assert response.status_code == 404
