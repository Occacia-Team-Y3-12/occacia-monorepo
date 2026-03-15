from __future__ import annotations

from datetime import timedelta

from app.common.utils import now_utc
from app.core.database import SessionLocal
from app.models.offering import Offering
from app.models.package_item import PackageItem
from app.models.recommendation_package import RecommendationPackage
from app.models.task_recommendation import TaskRecommendation
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
    budget_min: float | None = None,
    budget_max: float | None = None,
):
    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/tasks",
        json={
            "name": name,
            "quantity": quantity,
            "needsVendor": True,
            "vendorCategory": vendor_category,
            "budgetMin": budget_min,
            "budgetMax": budget_max,
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
            display_name="Celebration Cakes",
            category="cake",
            name="Chocolate Celebration Cake",
            description="Chocolate birthday cake with custom message",
            price=1500.0,
        )
        _create_vendor_offering(
            db,
            display_name="Luxury Cakes",
            category="cake",
            name="Luxury Designer Cake",
            description="Premium fondant cake",
            price=2600.0,
        )
        _create_vendor_offering(
            db,
            display_name="Budget Flowers",
            category="flowers",
            name="Simple Flowers",
            description="Basic bouquet",
            price=800.0,
        )
        _create_vendor_offering(
            db,
            display_name="Care Flowers",
            category="flowers",
            name="Get Well Flower Basket",
            description="Flower basket for visiting a sick mother",
            price=1200.0,
        )
        _create_vendor_offering(
            db,
            display_name="Luxury Flowers",
            category="flowers",
            name="Grand Orchid Arrangement",
            description="Premium orchid arrangement",
            price=2200.0,
        )
        db.commit()
    finally:
        db.close()


def test_generate_recommendation_packages_builds_three_variants(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a chocolate cake", vendor_category="cake")
    _create_task(auth_client, event_id, name="Bring flowers for mother", vendor_category="flowers", quantity=2)
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["eventId"] == event_id
    assert body["isExpired"] is False
    assert [pkg["packageType"] for pkg in body["packages"]] == ["BUDGET", "RECOMMENDED", "HIGH_QUALITY"]

    budget, recommended, high_quality = body["packages"]
    assert budget["packageTotalPrice"] == 2600.0
    assert recommended["packageTotalPrice"] == 3900.0
    assert high_quality["packageTotalPrice"] == 7000.0

    assert [item["offeringName"] for item in budget["items"]] == ["Basic Cake", "Simple Flowers"]
    assert [item["offeringName"] for item in recommended["items"]] == [
        "Chocolate Celebration Cake",
        "Get Well Flower Basket",
    ]
    assert [item["offeringName"] for item in high_quality["items"]] == [
        "Luxury Designer Cake",
        "Grand Orchid Arrangement",
    ]
    assert recommended["items"][1]["quantity"] == 2
    assert recommended["items"][1]["taskPrice"] == 2400.0
    assert [item["aiRank"] for item in recommended["items"]] == [1, 1]


def test_get_packages_returns_saved_generation(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a chocolate cake", vendor_category="cake")
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()
    generate = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert generate.status_code == 200, generate.text

    response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["packages"]) == 3
    assert all(pkg["eventId"] == event_id for pkg in body["packages"])


def test_regeneration_replaces_existing_generated_records(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a chocolate cake", vendor_category="cake")
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()

    first = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert first.status_code == 200, first.text
    first_package_ids = {pkg["packageId"] for pkg in first.json()["packages"]}

    second = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert second.status_code == 200, second.text
    second_package_ids = {pkg["packageId"] for pkg in second.json()["packages"]}

    assert first_package_ids != second_package_ids

    db = SessionLocal()
    try:
        assert db.query(RecommendationPackage).filter(RecommendationPackage.event_id == event_id).count() == 3
        assert db.query(PackageItem).filter(PackageItem.package_id.in_(list(second_package_ids))).count() == 3
        assert db.query(TaskRecommendation).filter(TaskRecommendation.event_id == event_id).count() == 3
    finally:
        db.close()


def test_get_packages_marks_expired_set(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Buy a chocolate cake", vendor_category="cake")
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()
    generate = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert generate.status_code == 200, generate.text

    db = SessionLocal()
    try:
        expired_at = now_utc() - timedelta(minutes=1)
        packages = db.query(RecommendationPackage).filter(RecommendationPackage.event_id == event_id).all()
        for package in packages:
            package.expires_at = expired_at
            db.add(package)
        db.commit()
    finally:
        db.close()

    response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["isExpired"] is True
    assert all(pkg["isExpired"] is True for pkg in body["packages"])


def test_generate_recommendations_fails_without_confirmed_tasks(auth_client):
    event_id = _create_event(auth_client)
    _seed_recommendation_offerings()

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")

    assert response.status_code == 409
    assert response.json()["detail"] == "Event must be active before generating packages"


def test_generate_recommendations_fails_when_task_has_no_valid_offerings(auth_client):
    event_id = _create_event(auth_client)
    _create_task(auth_client, event_id, name="Need a violinist", vendor_category="music")
    _confirm_tasks(auth_client, event_id)
    _seed_recommendation_offerings()

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")

    assert response.status_code == 400
    assert response.json()["detail"].startswith("No valid offerings available for task")

    db = SessionLocal()
    try:
        assert db.query(RecommendationPackage).filter(RecommendationPackage.event_id == event_id).count() == 0
        assert db.query(TaskRecommendation).filter(TaskRecommendation.event_id == event_id).count() == 0
    finally:
        db.close()
