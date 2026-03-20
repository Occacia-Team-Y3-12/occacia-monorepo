# ruff: noqa: S101

from app.core.database import SessionLocal
from app.models.offering import Offering
from app.models.recommendation_package import RecommendationPackage
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
        email=f"{vendor_name.lower().replace(' ', '-')}-{int(price)}@jit-uc16.test",
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


def test_whenCustomerCustomizesRecommendationPackage_shortlistCreateUpdateDelete_success(auth_client):
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
    cake_task_id = cake_task_response.json()["taskId"]

    confirm_response = auth_client.post(f"/api/v1/customers/events/{event_id}/tasks/confirm")
    assert confirm_response.status_code == 200
    assert confirm_response.json()["event"]["status"] == "ACTIVE"

    db = SessionLocal()
    try:
        for vendor_name, category, offering_name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Classic Cakes", "cake", "Classic Chocolate Cake", "Thoughtful chocolate cake", 1400.0),
            ("Luxury Cakes", "cake", "Luxury Designer Cake", "Premium fondant cake", 2200.0),
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

    shortlist_response = auth_client.get(
        f"/api/v1/customers/events/{event_id}/tasks/{cake_task_id}/recommendations"
    )
    assert shortlist_response.status_code == 200
    shortlist_body = shortlist_response.json()
    assert len(shortlist_body["items"]) == 3
    assert shortlist_body["items"][0]["taskId"] == cake_task_id

    package_detail_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}")
    assert package_detail_response.status_code == 200
    package_detail = package_detail_response.json()
    assert cake_task_id in package_detail["allowedOfferingsByTask"]

    custom_create_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages",
        json={
            "basePackageId": package_id,
            "items": [
                {
                    "taskId": cake_task_id,
                    "offeringId": package_detail["allowedOfferingsByTask"][cake_task_id][2]["offeringId"],
                }
            ],
        },
    )
    assert custom_create_response.status_code == 201
    custom_body = custom_create_response.json()
    custom_package_id = custom_body["packageId"]
    assert custom_body["packageType"] == "CUSTOM"
    assert custom_body["basePackageId"] == package_id
    assert custom_body["packageTotalPrice"] == 2200.0
    assert len(custom_body["items"]) == 1

    custom_update_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}",
        json={
            "items": [
                {
                    "taskId": cake_task_id,
                    "offeringId": package_detail["allowedOfferingsByTask"][cake_task_id][1]["offeringId"],
                },
            ],
        },
    )
    assert custom_update_response.status_code == 200
    updated_body = custom_update_response.json()
    assert len(updated_body["items"]) == 1
    assert updated_body["packageTotalPrice"] == updated_body["items"][0]["unitPrice"]

    custom_delete_response = auth_client.delete(
        f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}"
    )
    assert custom_delete_response.status_code == 204

    missing_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}")
    assert missing_response.status_code == 404

    db = SessionLocal()
    try:
        remaining_custom_package = (
            db.query(RecommendationPackage)
            .filter(RecommendationPackage.package_id == custom_package_id)
            .first()
        )
    finally:
        db.close()

    assert remaining_custom_package is None
