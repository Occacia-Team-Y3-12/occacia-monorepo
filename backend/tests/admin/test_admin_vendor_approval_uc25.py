"""
UC-25: Review & Approve Vendor Registration Test Suite

This test suite validates the admin vendor approval workflow:
- Viewing pending vendor registrations
- Approving/rejecting vendors
- Admin authorization checks
"""

import pytest


def test_admin_views_pending_vendors(admin_client):
    """UC-25: Admin can view pending vendor registrations"""
    response = admin_client.get("/api/v1/admin/vendors?approval_status=PENDING")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_approves_vendor(admin_client, pending_vendor):
    """UC-25: Admin can approve vendor registration"""
    response = admin_client.post(f"/api/v1/admin/vendors/{pending_vendor.id}/approve")
    assert response.status_code == 200
    data = response.json()
    assert data.get("approval_status") in ["ACTIVE", "APPROVED"]


def test_admin_rejects_vendor(admin_client, pending_vendor):
    """UC-25: Admin can reject vendor registration"""
    response = admin_client.post(
        f"/api/v1/admin/vendors/{pending_vendor.id}/reject",
        json={"reason": "Incomplete documentation"}
    )
    assert response.status_code == 200
    assert response.json().get("approval_status") == "REJECTED"


def test_non_admin_cannot_approve_vendor(active_customer, auth_token, client, pending_vendor):
    """UC-25: Non-admin users cannot approve vendors"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post(f"/api/v1/admin/vendors/{pending_vendor.id}/approve")
    # Admin endpoint rejects non-admin tokens with 401
    assert response.status_code in [401, 403]


def test_vendor_approval_requires_auth(client, pending_vendor):
    """UC-25: Vendor approval requires authentication"""
    response = client.post(f"/api/v1/admin/vendors/{pending_vendor.id}/approve")
    assert response.status_code in [401, 403]
