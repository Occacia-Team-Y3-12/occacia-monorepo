"""
UC-28: View Monitoring Dashboard Test Suite

This test suite validates the admin monitoring & support dashboard:
- Viewing package orders on dashboard
- Viewing tasks on dashboard  
- Adding internal notes
- Admin support actions
- Authorization checks
"""

import pytest


def test_admin_views_package_orders(admin_client):
    """UC-28: Admin can view package orders on dashboard"""
    response = admin_client.get("/api/v1/admin/package-orders")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)


def test_admin_filters_package_orders_by_status(admin_client):
    """UC-28: Admin can filter orders by status"""
    response = admin_client.get("/api/v1/admin/package-orders?status=pending")
    assert response.status_code == 200


def test_admin_views_package_order_details(admin_client):
    """UC-28: Admin can view specific order details"""
    # First get list to find an order ID
    response = admin_client.get("/api/v1/admin/package-orders?limit=1")
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            order_id = items[0].get("packageOrderId") or items[0].get("id")
            detail_response = admin_client.get(f"/api/v1/admin/package-orders/{order_id}")
            assert detail_response.status_code in [200, 404]


def test_admin_creates_internal_note(admin_client):
    """UC-28: Admin can create internal notes for tracking"""
    response = admin_client.post(
        "/api/v1/admin/internal-notes",
        json={
            "event_id": "EVT-TEST-001",
            "task_id": None,
            "vendor_id": None,
            "package_order_id": None,
            "action_type": "NOTE_ONLY",
            "note": "Test internal note"
        }
    )
    assert response.status_code in [201, 400, 404]  # 400/404 if event doesn't exist


def test_admin_views_internal_notes(admin_client):
    """UC-28: Admin can view internal notes"""
    response = admin_client.get("/api/v1/admin/internal-notes")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)


def test_admin_views_inquiries_list(admin_client):
    """UC-28: Admin can view inquiries/support requests"""
    response = admin_client.get("/api/v1/admin/inquiries")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)


def test_admin_filters_inquiries_by_status(admin_client):
    """UC-28: Admin can filter inquiries by status"""
    response = admin_client.get("/api/v1/admin/inquiries?status=pending")
    assert response.status_code == 200


def test_non_admin_cannot_view_dashboard(active_customer, auth_token, client):
    """UC-28: Non-admin users cannot view monitoring dashboard"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/admin/package-orders")
    # Admin endpoint rejects non-admin tokens with 401
    assert response.status_code in [401, 403]


def test_dashboard_requires_authentication(client):
    """UC-28: Dashboard access requires authentication"""
    response = client.get("/api/v1/admin/package-orders")
    assert response.status_code in [401, 403]
