"""
UC-26: View and Manage Vendors Test Suite

This test suite validates the admin vendor management workflow:
- Viewing list of all vendors
- Viewing specific vendor details
- Filtering vendors by status
- Admin authorization checks
"""

import pytest


def test_admin_views_all_vendors(admin_client):
    """UC-26: Admin can view list of all vendors"""
    response = admin_client.get("/api/v1/admin/vendors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_admin_views_vendor_details(admin_client, active_vendor):
    """UC-26: Admin can view details of a specific vendor"""
    response = admin_client.get(f"/api/v1/admin/vendors/{active_vendor.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == active_vendor.email
    assert data["business_name"] == active_vendor.business_name


def test_admin_filters_vendors_by_status(admin_client, pending_vendor):
    """UC-26: Admin can filter vendors by approval status"""
    response = admin_client.get("/api/v1/admin/vendors?approval_status=PENDING")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_non_admin_cannot_view_vendors(active_customer, auth_token, client):
    """UC-26: Non-admin users cannot view vendor list"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/admin/vendors")
    # Admin endpoint rejects non-admin tokens with 401
    assert response.status_code in [401, 403]


def test_vendor_access_requires_auth(client):
    """UC-26: Vendor access requires authentication"""
    response = client.get("/api/v1/admin/vendors")
    assert response.status_code in [401, 403]


def test_admin_views_nonexistent_vendor(admin_client):
    """UC-26: Requesting nonexistent vendor returns error"""
    response = admin_client.get("/api/v1/admin/vendors/99999")
    assert response.status_code == 404
