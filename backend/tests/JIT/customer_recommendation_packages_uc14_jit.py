# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.offering import Offering
from app.models.package_item import PackageItem
from app.models.recommendation_package import RecommendationPackage
from app.models.task_recommendation import TaskRecommendation
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
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit.test",
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


def test_whenCustomerGeneratesRecommendationPackages_postRecommendationsAndGetPackages_success(auth_client):
    create_response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": "Visit Sick Mother"},
    )
    assert create_response.status_code == 201
    event_id = create_response.json()["eventId"]

    cake_task = auth_client.post(
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
    assert cake_task.status_code == 201

    flowers_task = auth_client.post(
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
    assert flowers_task.status_code == 201

    confirm_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert confirm_response.status_code == 200
    assert confirm_response.json()["event"]["status"] == "ACTIVE"

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
            vendor_name="Celebration Cakes",
            category="cake",
            offering_name="Chocolate Celebration Cake",
            description="Chocolate birthday cake with custom message",
            price=1500.0,
        )
        _seed_offering(
            db,
            vendor_name="Luxury Cakes",
            category="cake",
            offering_name="Luxury Designer Cake",
            description="Premium fondant cake",
            price=2600.0,
        )
        _seed_offering(
            db,
            vendor_name="Budget Flowers",
            category="flowers",
            offering_name="Simple Flowers",
            description="Basic bouquet",
            price=800.0,
        )
        _seed_offering(
            db,
            vendor_name="Care Flowers",
            category="flowers",
            offering_name="Get Well Flower Basket",
            description="Flower basket for visiting a sick mother",
            price=1200.0,
        )
        _seed_offering(
            db,
            vendor_name="Luxury Flowers",
            category="flowers",
            offering_name="Grand Orchid Arrangement",
            description="Premium orchid arrangement",
            price=2200.0,
        )
        db.commit()
    finally:
        db.close()

    generate_response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert generate_response.status_code == 200
    generated_body = generate_response.json()
    assert [pkg["packageType"] for pkg in generated_body["packages"]] == [
        "BUDGET",
        "RECOMMENDED",
        "HIGH_QUALITY",
    ]
    assert generated_body["packages"][1]["packageTotalPrice"] == 3900.0

    packages_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages")
    assert packages_response.status_code == 200
    packages_body = packages_response.json()
    assert packages_body["eventId"] == event_id
    assert packages_body["isExpired"] is False
    assert len(packages_body["packages"]) == 3
    assert packages_body["packages"][0]["items"][0]["offeringName"] == "Basic Cake"
    assert packages_body["packages"][1]["items"][0]["offeringName"] == "Chocolate Celebration Cake"
    assert packages_body["packages"][2]["items"][1]["offeringName"] == "Grand Orchid Arrangement"

    db = SessionLocal()
    try:
        package_count = db.query(RecommendationPackage).filter(RecommendationPackage.event_id == event_id).count()
        package_item_count = (
            db.query(PackageItem)
            .join(RecommendationPackage, RecommendationPackage.package_id == PackageItem.package_id)
            .filter(RecommendationPackage.event_id == event_id)
            .count()
        )
        shortlist_count = db.query(TaskRecommendation).filter(TaskRecommendation.event_id == event_id).count()
    finally:
        db.close()

    assert package_count == 3
    assert package_item_count == 6
    assert shortlist_count == 6
