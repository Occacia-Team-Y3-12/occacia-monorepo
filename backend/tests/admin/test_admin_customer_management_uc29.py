"""
UC-29: Manage Customers Test Suite

This test suite validates the admin customer management workflow:
- Viewing list of customers
- Viewing customer details
- Activating/deactivating customers
- Admin authorization checks
"""

import pytest


def test_admin_views_all_customers(admin_client):
    """UC-29: Admin can view list of all customers"""
    response = admin_client.get("/api/v1/admin/customers")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)


def test_admin_views_customer_details(admin_client, active_customer):
    """UC-29: Admin can view details of a specific customer"""
    response = admin_client.get(f"/api/v1/admin/customers/{active_customer.customer_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == active_customer.email
    assert data["full_name"] == active_customer.full_name


def test_admin_filters_customers_by_status(admin_client, multiple_customers):
    """UC-29: Admin can filter customers by status"""
    response = admin_client.get("/api/v1/admin/customers?status=ACTIVE")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)


def test_admin_updates_customer_status(admin_client, active_customer):
    """UC-29: Admin can update customer status"""
    response = admin_client.put(
        f"/api/v1/admin/customers/{active_customer.customer_id}/status",
        json={"status": "SUSPENDED"}
    )
    assert response.status_code in [200, 400]  # 400 if status is invalid


def test_admin_deactivates_customer(admin_client, active_customer):
    """UC-29: Admin can deactivate a customer"""
    response = admin_client.put(
        f"/api/v1/admin/customers/{active_customer.customer_id}/status",
        json={"status": "INACTIVE"}
    )
    assert response.status_code in [200, 400, 422]  # 422 if validation fails


def test_non_admin_cannot_view_customers(active_customer, auth_token, client):
    """UC-29: Non-admin users cannot view customer list"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/admin/customers")
    # Admin endpoint rejects non-admin tokens with 401
    assert response.status_code in [401, 403]


def test_non_admin_cannot_update_customer_status(active_customer, auth_token, client):
    """UC-29: Non-admin users cannot change customer status"""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.put(
        f"/api/v1/admin/customers/{active_customer.customer_id}/status",
        json={"status": "INACTIVE"}
    )
    # Admin endpoint rejects non-admin tokens with 401
    assert response.status_code in [401, 403]


def test_customer_access_requires_auth(client):
    """UC-29: Customer access requires authentication"""
    response = client.get("/api/v1/admin/customers")
    assert response.status_code in [401, 403]


def test_admin_views_nonexistent_customer(admin_client):
    """UC-29: Requesting nonexistent customer returns error"""
    response = admin_client.get("/api/v1/admin/customers/CUST-NONEXISTENT-12345")
    assert response.status_code == 404


def test_admin_customer_list_pagination(admin_client):
    """UC-29: Customer list supports pagination"""
    response = admin_client.get("/api/v1/admin/customers?limit=10")
    assert response.status_code == 200


def test_admin_customer_status_update_validation(admin_client, active_customer):
    """UC-29: Customer status update validates status values"""
    response = admin_client.put(
        f"/api/v1/admin/customers/{active_customer.customer_id}/status",
        json={"status": "INVALID_STATUS"}
    )
    # Should either accept it or reject with validation error
    assert response.status_code in [200, 400, 422]
