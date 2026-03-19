# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.offering import Offering
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
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit-uc15.test",
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


def test_whenCustomerViewsRecommendationPackageDetails_getPackageById_success(auth_client):
    # 1. Setup Event and Tasks
    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": "Visit Sick Mother"},
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

    auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": "Buy a chocolate cake for mother",
            "quantity": 1,
            "needsVendor": True,
            "vendorCategory": "cake",
            "currency": "LKR",
        },
    )
    auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": "Bring flowers for mother",
            "quantity": 2,
            "needsVendor": True,
            "vendorCategory": "flowers",
            "currency": "LKR",
        },
    )

    # 2. Activate event by confirming tasks
    confirm_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert confirm_response.status_code == 200

    # 3. Seed offerings
    db = SessionLocal()
    try:
        _seed_offering(
            db,
            vendor_name="Budget Cakes",
            category="cake",
            offering_name="Basic Cake",
            description="Simple vanilla cake",
            price=1000.0,
        )
        _seed_offering(
            db,
            vendor_name="Care Flowers",
            category="flowers",
            offering_name="Get Well Flower Basket",
            description="Flower basket for visiting a sick mother",
            price=1200.0,
        )
        db.commit()
    finally:
        db.close()

    # 4. Generate recommendations
    generate_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert generate_response.status_code == 200
    packages = generate_response.json()["packages"]
    package_id = packages[0]["packageId"]

    # 5. Get individual package details (UC-15)
    detail_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}")
    assert detail_response.status_code == 200
    
    body = detail_response.json()
    assert body["packageId"] == package_id
    assert body["eventId"] == event_id
    assert len(body["items"]) == 2
    
    # 6. Verify item details (UC-15 requirements)
    cake_item = next(item for item in body["items"] if item["offeringCategory"] == "cake")
    assert cake_item["taskName"] == "Buy a chocolate cake for mother"
    assert cake_item["offeringName"] == "Basic Cake"
    assert cake_item["vendorName"] == "Budget Cakes"
    assert cake_item["unitPrice"] == 1000.0
    assert cake_item["taskPrice"] == 1000.0
    
    flower_item = next(item for item in body["items"] if item["offeringCategory"] == "flowers")
    assert flower_item["taskName"] == "Bring flowers for mother"
    assert flower_item["offeringName"] == "Get Well Flower Basket"
    assert flower_item["vendorName"] == "Care Flowers"
    assert flower_item["unitPrice"] == 1200.0
    assert flower_item["taskPrice"] == 2400.0 # quantity 2
    
    assert body["packageTotalPrice"] == 3400.0
