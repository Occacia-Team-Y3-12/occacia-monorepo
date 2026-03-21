from __future__ import annotations

from app.core.database import SessionLocal
from app.models.recommendation_package import RecommendationPackage
from app.models.vendor import Vendor
from app.models.offering import Offering


def _create_event(auth_client, title: str = "Customize Gift Package") -> str:
    response = auth_client.post(
        "/api/v1/customers/events",
        json={"eventType": "Family", "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()["eventId"]


def _create_task(auth_client, event_id: str, *, name: str, vendor_category: str, quantity: int = 1) -> str:
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
) -> Offering:
    email = f"{display_name.lower().replace(' ', '-')}-{price}@test.com"

    # get-or-create: avoids UNIQUE constraint on vendors.email across test runs
    vendor = db.query(Vendor).filter(Vendor.email == email).first()
    if not vendor:
        vendor = Vendor(
            business_name=display_name,
            display_name=display_name,
            email=email,
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
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.add(offering)
    db.flush()
    return offering


def _seed_offerings():
    db = SessionLocal()
    try:
        for display_name, category, name, description, price in (
            ("Budget Cakes", "cake", "Basic Cake", "Simple vanilla cake", 1000.0),
            ("Classic Cakes", "cake", "Classic Chocolate Cake", "Chocolate cake", 1400.0),
            ("Luxury Cakes", "cake", "Luxury Designer Cake", "Premium fondant cake", 2200.0),
            ("Budget Flowers", "flowers", "Simple Flowers", "Basic bouquet", 700.0),
            ("Care Flowers", "flowers", "Care Basket", "Flower basket", 1100.0),
            ("Luxury Flowers", "flowers", "Grand Orchid Arrangement", "Premium orchids", 1800.0),
        ):
            _create_vendor_offering(
                db,
                display_name=display_name,
                category=category,
                name=name,
                description=description,
                price=price,
            )
        db.commit()
    finally:
        db.close()


def _generate_packages(auth_client):
    event_id = _create_event(auth_client)
    cake_task_id = _create_task(auth_client, event_id, name="Buy a cake", vendor_category="cake")
    flower_task_id = _create_task(auth_client, event_id, name="Bring flowers", vendor_category="flowers", quantity=2)
    _confirm_tasks(auth_client, event_id)
    _seed_offerings()

    response = auth_client.post(f"/api/v1/customers/events/{event_id}/recommendations")
    assert response.status_code == 200, response.text
    package_id = response.json()["packages"][1]["packageId"]
    return event_id, package_id, cake_task_id, flower_task_id


def test_get_task_recommendations_returns_shortlist(auth_client):
    event_id, _, cake_task_id, _ = _generate_packages(auth_client)

    response = auth_client.get(f"/api/v1/customers/events/{event_id}/tasks/{cake_task_id}/recommendations")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["items"]) == 3
    assert [item["rank"] for item in body["items"]] == [1, 2, 3]
    assert all(item["taskId"] == cake_task_id for item in body["items"])


def test_create_custom_package_replaces_vendor_and_removes_task(auth_client):
    event_id, package_id, cake_task_id, flower_task_id = _generate_packages(auth_client)

    detail_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail_body = detail_response.json()
    cake_shortlist = detail_body["allowedOfferingsByTask"][cake_task_id]
    replacement_cake_id = cake_shortlist[2]["offeringId"]

    response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages",
        json={
            "basePackageId": package_id,
            "items": [{"taskId": cake_task_id, "offeringId": replacement_cake_id}],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["packageType"] == "CUSTOM"
    assert body["isCustomized"] is True
    assert body["basePackageId"] == package_id
    assert len(body["items"]) == 1
    assert body["items"][0]["taskId"] == cake_task_id
    assert body["items"][0]["offeringId"] == replacement_cake_id
    assert body["packageTotalPrice"] == 2200.0
    assert flower_task_id not in body["allowedOfferingsByTask"]

    db = SessionLocal()
    try:
        saved = (
            db.query(RecommendationPackage)
            .filter(RecommendationPackage.package_id == body["packageId"])
            .first()
        )
        assert saved is not None
        assert saved.base_package_id == package_id
        assert saved.is_customized is True
    finally:
        db.close()


def test_update_custom_package_recalculates_total(auth_client):
    event_id, package_id, cake_task_id, flower_task_id = _generate_packages(auth_client)

    package_detail = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}").json()
    cake_shortlist = package_detail["allowedOfferingsByTask"][cake_task_id]
    flower_shortlist = package_detail["allowedOfferingsByTask"][flower_task_id]

    create_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages",
        json={
            "basePackageId": package_id,
            "items": [{"taskId": cake_task_id, "offeringId": cake_shortlist[0]["offeringId"]}],
        },
    )
    custom_package_id = create_response.json()["packageId"]

    update_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}",
        json={
            "items": [
                {"taskId": cake_task_id, "offeringId": cake_shortlist[1]["offeringId"]},
                {"taskId": flower_task_id, "offeringId": flower_shortlist[2]["offeringId"]},
            ],
        },
    )

    assert update_response.status_code == 200, update_response.text
    body = update_response.json()
    assert len(body["items"]) == 2
    assert body["packageTotalPrice"] == 5000.0
    assert {item["taskId"] for item in body["items"]} == {cake_task_id, flower_task_id}


def test_invalid_customization_keeps_package_unchanged(auth_client):
    event_id, package_id, cake_task_id, _ = _generate_packages(auth_client)

    package_detail = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}").json()
    cake_shortlist = package_detail["allowedOfferingsByTask"][cake_task_id]

    create_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages",
        json={
            "basePackageId": package_id,
            "items": [{"taskId": cake_task_id, "offeringId": cake_shortlist[0]["offeringId"]}],
        },
    )
    custom_package_id = create_response.json()["packageId"]

    invalid_response = auth_client.put(
        f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}",
        json={"items": [{"taskId": cake_task_id, "offeringId": "OFF-NOT-IN-SHORTLIST"}]},
    )

    assert invalid_response.status_code == 400, invalid_response.text

    detail_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}")
    body = detail_response.json()
    assert body["items"] == create_response.json()["items"]
    assert body["packageTotalPrice"] == create_response.json()["packageTotalPrice"]


def test_delete_custom_package(auth_client):
    event_id, package_id, cake_task_id, _ = _generate_packages(auth_client)

    package_detail = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{package_id}").json()
    cake_shortlist = package_detail["allowedOfferingsByTask"][cake_task_id]

    create_response = auth_client.post(
        f"/api/v1/customers/events/{event_id}/packages",
        json={
            "basePackageId": package_id,
            "items": [{"taskId": cake_task_id, "offeringId": cake_shortlist[0]["offeringId"]}],
        },
    )
    custom_package_id = create_response.json()["packageId"]

    delete_response = auth_client.delete(f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}")
    assert delete_response.status_code == 204, delete_response.text

    get_response = auth_client.get(f"/api/v1/customers/events/{event_id}/packages/{custom_package_id}")
    assert get_response.status_code == 404