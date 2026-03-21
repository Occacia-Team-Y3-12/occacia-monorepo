# ruff: noqa: S101

from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.admin import Admin
from app.models.vendor import Vendor


def test_admin_review_approve_vendor_registration_uc25_full_workflow(client, monkeypatch):
    """
    UC-25: Review & Approve Vendor Registration
    
    Scenario:
    1. Admin logs in
    2. Admin lists pending vendor registrations
    3. Admin views vendor detail
    4. Admin approves one vendor
    5. Admin rejects another vendor
    6. Admin verifies state changes persisted
    """
    monkeypatch.setattr("app.routers.v1.admin_router._send_approval_email", lambda v: None)
    monkeypatch.setattr("app.routers.v1.admin_router._send_rejection_email", lambda v, r: None)

    # Setup: Create admin and pending vendors
    db = SessionLocal()
    try:
        admin = Admin(
            email="admin@occacia.com",
            password_hash=get_password_hash("Admin1234!"),
            staff_role="staff",
        )
        db.add(admin)
        db.flush()
        admin_id = admin.admin_id

        vendor_to_approve = Vendor(
            business_name="Premium Catering Services",
            display_name="Premium Catering",
            email="premium-catering@test.com",
            phone="+94771234567",
            location_base="Colombo",
            approval_status="PENDING",
            is_verified=False,
        )
        vendor_to_reject = Vendor(
            business_name="Budget Event Planning",
            display_name="Budget Events",
            email="budget-events@test.com",
            phone="+94779876543",
            location_base="Kandy",
            approval_status="PENDING",
            is_verified=False,
        )
        vendor_already_approved = Vendor(
            business_name="Established Venue",
            display_name="Established Venue",
            email="established@test.com",
            approval_status="APPROVED",
            is_verified=True,
        )
        db.add(vendor_to_approve)
        db.add(vendor_to_reject)
        db.add(vendor_already_approved)
        db.commit()
        db.refresh(vendor_to_approve)
        db.refresh(vendor_to_reject)
        db.refresh(vendor_already_approved)

        vendor_approve_id = vendor_to_approve.id
        vendor_reject_id = vendor_to_reject.id
        vendor_approved_id = vendor_already_approved.id
    finally:
        db.close()

    # Step 1: Admin authentication
    admin_token = create_access_token(data={"sub": admin_id, "type": "admin"})
    auth_header = {"Authorization": f"Bearer {admin_token}"}

    # Step 2: List pending vendor registrations
    list_response = client.get("/api/v1/admin/vendors?approval_status=PENDING", headers=auth_header)
    assert list_response.status_code == 200, list_response.text
    pending_vendors = list_response.json()
    assert len(pending_vendors) == 2
    assert all(v["approval_status"] == "PENDING" for v in pending_vendors)
    assert any(v["business_name"] == "Premium Catering Services" for v in pending_vendors)
    assert any(v["business_name"] == "Budget Event Planning" for v in pending_vendors)

    # Step 3: Get vendor detail for the one to approve
    detail_response = client.get(f"/api/v1/admin/vendors/{vendor_approve_id}", headers=auth_header)
    assert detail_response.status_code == 200, detail_response.text
    vendor_detail = detail_response.json()
    assert vendor_detail["business_name"] == "Premium Catering Services"
    assert vendor_detail["approval_status"] == "PENDING"
    assert vendor_detail["is_verified"] is False
    assert vendor_detail["email"] == "premium-catering@test.com"
    assert vendor_detail["location_base"] == "Colombo"

    # Step 4: Approve the first vendor
    approve_response = client.post(f"/api/v1/admin/vendors/{vendor_approve_id}/approve", headers=auth_header)
    assert approve_response.status_code == 200, approve_response.text
    approved_vendor = approve_response.json()
    assert approved_vendor["approval_status"] == "APPROVED"
    assert approved_vendor["is_verified"] is True
    assert approved_vendor["approved_at"] is not None

    # Step 5: Reject the second vendor
    reject_response = client.post(
        f"/api/v1/admin/vendors/{vendor_reject_id}/reject",
        headers=auth_header,
        json={"reason": "Incomplete business documentation"},
    )
    assert reject_response.status_code == 200, reject_response.text
    rejected_vendor = reject_response.json()
    assert rejected_vendor["approval_status"] == "REJECTED"
    assert rejected_vendor["is_verified"] is False

    # Step 6: Verify pending list now empty
    list_after_response = client.get("/api/v1/admin/vendors?approval_status=PENDING", headers=auth_header)
    assert list_after_response.status_code == 200
    assert len(list_after_response.json()) == 0

    # Step 7: Verify approved list contains the approved vendor
    approved_list_response = client.get("/api/v1/admin/vendors?approval_status=APPROVED", headers=auth_header)
    assert approved_list_response.status_code == 200
    approved_list = approved_list_response.json()
    assert len(approved_list) == 2  # Our newly approved + the pre-existing one
    assert any(v["id"] == vendor_approve_id for v in approved_list)

    # Step 8: Verify rejected list contains the rejected vendor
    rejected_list_response = client.get("/api/v1/admin/vendors?approval_status=REJECTED", headers=auth_header)
    assert rejected_list_response.status_code == 200
    rejected_list = rejected_list_response.json()
    assert len(rejected_list) == 1
    assert rejected_list[0]["id"] == vendor_reject_id

    # Step 9: Attempt to approve already approved vendor (should fail)
    double_approve_response = client.post(f"/api/v1/admin/vendors/{vendor_approved_id}/approve", headers=auth_header)
    assert double_approve_response.status_code == 400
    assert "already approved" in double_approve_response.json()["detail"]

    # Step 10: Attempt to reject already rejected vendor (should fail)
    double_reject_response = client.post(
        f"/api/v1/admin/vendors/{vendor_reject_id}/reject",
        headers=auth_header,
        json={"reason": "Another reason"},
    )
    assert double_reject_response.status_code == 400
    assert "already rejected" in double_reject_response.json()["detail"]

    # Step 11: Verify database state
    db = SessionLocal()
    try:
        approved = db.query(Vendor).filter(Vendor.id == vendor_approve_id).first()
        rejected = db.query(Vendor).filter(Vendor.id == vendor_reject_id).first()

        assert approved.approval_status == "APPROVED"
        assert approved.is_verified is True
        assert approved.approved_at is not None

        assert rejected.approval_status == "REJECTED"
        assert rejected.is_verified is False
    finally:
        db.close()

    # Step 12: Verify non-admin cannot access these endpoints
    customer_token = create_access_token(data={"sub": "customer@test.com"})
    unauthorized_response = client.get(
        "/api/v1/admin/vendors",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert unauthorized_response.status_code == 401
