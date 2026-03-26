from __future__ import annotations


def test_customer_inquiries_requires_auth(client):
    r = client.get("/api/v1/customers/inquiries")
    assert r.status_code == 401


def test_vendor_inquiries_requires_auth(client):
    r = client.get("/api/v1/vendors/inquiries")
    assert r.status_code == 401


def test_admin_inquiries_requires_auth(client):
    r = client.get("/api/v1/admin/inquiries")
    assert r.status_code == 401
