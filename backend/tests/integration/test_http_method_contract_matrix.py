from __future__ import annotations

import uuid

import pytest


EVENT_ID = str(uuid.uuid4())
TASK_ID = str(uuid.uuid4())
PACKAGE_ID = str(uuid.uuid4())
PACKAGE_ORDER_ID = str(uuid.uuid4())
INQUIRY_ID = str(uuid.uuid4())
OFFERING_ID = str(uuid.uuid4())
VENDOR_ID = str(uuid.uuid4())
CUSTOMER_ID = str(uuid.uuid4())
ORG_ID = str(uuid.uuid4())
FULFILLMENT_REQUEST_ID = str(uuid.uuid4())
PERSONA_ID = str(uuid.uuid4())


CASES = [
    ("GET", "/api/v1/auth/customer/register"),
    ("PUT", "/api/v1/auth/customer/register"),
    ("GET", "/api/v1/auth/customer/login"),
    ("PUT", "/api/v1/auth/customer/login"),
    ("GET", "/api/v1/auth/customer/logout"),
    ("PUT", "/api/v1/auth/customer/logout"),
    ("GET", "/api/v1/auth/customer/token/refresh"),
    ("PUT", "/api/v1/auth/customer/token/refresh"),
    ("GET", "/api/v1/auth/customer/password/forgot"),
    ("PUT", "/api/v1/auth/customer/password/forgot"),
    ("GET", "/api/v1/auth/customer/password/verify-otp"),
    ("PUT", "/api/v1/auth/customer/password/verify-otp"),
    ("GET", "/api/v1/auth/customer/password/forgot/resend-otp"),
    ("PUT", "/api/v1/auth/customer/password/forgot/resend-otp"),
    ("GET", "/api/v1/auth/customer/password/reset"),
    ("PUT", "/api/v1/auth/customer/password/reset"),
    ("GET", "/api/v1/auth/vendor/register"),
    ("PUT", "/api/v1/auth/vendor/register"),
    ("GET", "/api/v1/auth/vendor/login"),
    ("PUT", "/api/v1/auth/vendor/login"),
    ("GET", "/api/v1/auth/vendor/logout"),
    ("PUT", "/api/v1/auth/vendor/logout"),
    ("GET", "/api/v1/auth/vendor/token/refresh"),
    ("PUT", "/api/v1/auth/vendor/token/refresh"),
    ("GET", "/api/v1/auth/vendor/password/forgot"),
    ("PUT", "/api/v1/auth/vendor/password/forgot"),
    ("GET", "/api/v1/auth/vendor/password/verify-otp"),
    ("PUT", "/api/v1/auth/vendor/password/verify-otp"),
    ("GET", "/api/v1/auth/vendor/password/forgot/resend-otp"),
    ("PUT", "/api/v1/auth/vendor/password/forgot/resend-otp"),
    ("GET", "/api/v1/auth/vendor/password/reset"),
    ("PUT", "/api/v1/auth/vendor/password/reset"),
    ("GET", "/api/v1/auth/admin/login"),
    ("PUT", "/api/v1/auth/admin/login"),
    ("GET", "/api/v1/auth/admin/login/verify-otp"),
    ("PUT", "/api/v1/auth/admin/login/verify-otp"),
    ("GET", "/api/v1/auth/admin/logout"),
    ("PUT", "/api/v1/auth/admin/logout"),
    ("GET", "/api/v1/auth/admin/token/refresh"),
    ("PUT", "/api/v1/auth/admin/token/refresh"),
    ("GET", "/api/v1/auth/admin/password/forgot"),
    ("PUT", "/api/v1/auth/admin/password/forgot"),
    ("GET", "/api/v1/auth/admin/password/verify-otp"),
    ("PUT", "/api/v1/auth/admin/password/verify-otp"),
    ("GET", "/api/v1/auth/admin/password/reset"),
    ("PUT", "/api/v1/auth/admin/password/reset"),
    ("POST", "/api/v1/customers/me"),
    ("DELETE", "/api/v1/customers/me"),
    ("POST", "/api/v1/vendors/me"),
    ("DELETE", "/api/v1/vendors/me"),
    ("POST", "/api/v1/admin/me"),
    ("DELETE", "/api/v1/admin/me"),
    ("PUT", "/api/v1/customers/personas"),
    ("PATCH", "/api/v1/customers/personas"),
    ("PUT", "/api/v1/customers/personas/confirmed"),
    ("POST", f"/api/v1/customers/personas/{PERSONA_ID}"),
    ("PATCH", f"/api/v1/customers/personas/{PERSONA_ID}"),
    ("PUT", f"/api/v1/customers/personas/{PERSONA_ID}/confirm"),
    ("PATCH", f"/api/v1/customers/personas/{PERSONA_ID}/confirm"),
    ("PATCH", "/api/v1/customers/events"),
    ("PUT", "/api/v1/customers/events"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}"),
    ("DELETE", f"/api/v1/customers/events/{EVENT_ID}/personas"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/chat"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/chat"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/summarize"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/summarize"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/messages"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/tasks"),
    ("PATCH", f"/api/v1/customers/events/{EVENT_ID}/tasks"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}"),
    ("PATCH", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/tasks/confirm"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/tasks/confirm"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/reassign"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/reassign"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/recommendations"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/recommendations"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/recommendations"),
    ("PATCH", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/recommendations"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/packages"),
    ("PATCH", f"/api/v1/customers/events/{EVENT_ID}/packages"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}"),
    ("PATCH", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}/confirm"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}/confirm"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/package-orders"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/package-orders"),
    ("POST", "/api/v1/customers/package-orders"),
    ("PUT", "/api/v1/customers/package-orders"),
    ("POST", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}"),
    ("PUT", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}"),
    ("GET", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}/cancel"),
    ("POST", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}/cancel"),
    ("PUT", "/api/v1/customers/inquiries"),
    ("PATCH", "/api/v1/customers/inquiries"),
    ("POST", f"/api/v1/customers/inquiries/{INQUIRY_ID}"),
    ("PUT", f"/api/v1/customers/inquiries/{INQUIRY_ID}"),
    ("POST", "/api/v1/vendors/inquiries"),
    ("PUT", "/api/v1/vendors/inquiries"),
    ("POST", f"/api/v1/vendors/inquiries/{INQUIRY_ID}"),
    ("PUT", f"/api/v1/vendors/inquiries/{INQUIRY_ID}"),
    ("PUT", "/api/v1/vendors/offerings"),
    ("PATCH", "/api/v1/vendors/offerings"),
    ("POST", f"/api/v1/vendors/offerings/{OFFERING_ID}"),
    ("PATCH", f"/api/v1/vendors/offerings/{OFFERING_ID}"),
    ("PUT", "/api/v1/vendors/fulfillment-requests"),
    ("POST", "/api/v1/vendors/fulfillment-requests"),
    ("PUT", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}"),
    ("DELETE", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}"),
    ("GET", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}/response"),
    ("PUT", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}/response"),
    ("POST", "/api/v1/vendors/tasks"),
    ("DELETE", "/api/v1/vendors/tasks"),
    ("POST", f"/api/v1/vendors/tasks/{TASK_ID}"),
    ("DELETE", f"/api/v1/vendors/tasks/{TASK_ID}"),
    ("PUT", "/api/v1/vendors/me/packages"),
    ("PATCH", "/api/v1/vendors/me/packages"),
    ("GET", "/api/v1/vendors/me/packages/1"),
    ("POST", "/api/v1/vendors/me/packages/1"),
    ("POST", "/api/v1/admin/vendors"),
    ("PUT", "/api/v1/admin/vendors"),
    ("POST", f"/api/v1/admin/vendors/{VENDOR_ID}"),
    ("PUT", f"/api/v1/admin/vendors/{VENDOR_ID}"),
    ("GET", f"/api/v1/admin/vendors/{VENDOR_ID}/approve"),
    ("PUT", f"/api/v1/admin/vendors/{VENDOR_ID}/approve"),
    ("GET", f"/api/v1/admin/vendors/{VENDOR_ID}/reject"),
    ("PUT", f"/api/v1/admin/vendors/{VENDOR_ID}/reject"),
    ("POST", "/api/v1/admin/vendors/stats/pending"),
    ("PUT", "/api/v1/admin/vendors/stats/pending"),
    ("POST", "/api/v1/admin/customers"),
    ("PUT", "/api/v1/admin/customers"),
    ("POST", f"/api/v1/admin/customers/{CUSTOMER_ID}"),
    ("PUT", f"/api/v1/admin/customers/{CUSTOMER_ID}"),
    ("GET", f"/api/v1/admin/customers/{CUSTOMER_ID}/status"),
    ("POST", f"/api/v1/admin/customers/{CUSTOMER_ID}/status"),
    ("POST", "/api/v1/admin/organizations"),
    ("PUT", "/api/v1/admin/organizations"),
    ("POST", f"/api/v1/admin/organizations/{ORG_ID}"),
    ("PUT", f"/api/v1/admin/organizations/{ORG_ID}"),
    ("GET", f"/api/v1/admin/organizations/{ORG_ID}/status"),
    ("POST", f"/api/v1/admin/organizations/{ORG_ID}/status"),
    ("POST", "/api/v1/admin/inquiries"),
    ("PUT", "/api/v1/admin/inquiries"),
    ("POST", f"/api/v1/admin/inquiries/{INQUIRY_ID}"),
    ("DELETE", f"/api/v1/admin/inquiries/{INQUIRY_ID}"),
    ("PUT", "/api/v1/admin/internal-notes"),
    ("PATCH", "/api/v1/admin/internal-notes"),
    ("POST", "/api/v1/admin/package-orders"),
    ("PUT", "/api/v1/admin/package-orders"),
    ("POST", f"/api/v1/admin/package-orders/{PACKAGE_ORDER_ID}"),
    ("PUT", f"/api/v1/admin/package-orders/{PACKAGE_ORDER_ID}"),
    ("POST", "/api/v1/admin/tasks"),
    ("PUT", "/api/v1/admin/tasks"),
    ("POST", f"/api/v1/admin/tasks/{TASK_ID}"),
    ("DELETE", f"/api/v1/admin/tasks/{TASK_ID}"),
    ("POST", f"/api/v1/admin/tasks/{TASK_ID}/fulfillment-requests"),
    ("PUT", f"/api/v1/admin/tasks/{TASK_ID}/fulfillment-requests"),
    ("POST", "/api/v1/admin/dashboard"),
    ("PUT", "/api/v1/admin/dashboard"),
    ("POST", "/api/v1/event-types"),
    ("PUT", "/api/v1/event-types"),
    ("POST", "/api/v1/event-templates"),
    ("PUT", "/api/v1/event-templates"),
    ("POST", "/api/v1/offering-categories"),
    ("PUT", "/api/v1/offering-categories"),
    ("POST", "/api/v1/health"),
    ("PUT", "/api/v1/health"),
    ("POST", "/api/v1/version"),
    ("PUT", "/api/v1/version"),
]


def _payload_for(path: str):
    if path.endswith("/auth/customer/register"):
        return {"fullName": "A", "email": "a@test.com", "password": "Password123!"}
    if path.endswith("/auth/customer/login"):
        return {"email": "a@test.com", "password": "Password123!"}
    if path.endswith("/auth/customer/token/refresh"):
        return {"refreshToken": "x"}
    if path.endswith("/auth/customer/password/forgot"):
        return {"email": "a@test.com"}
    if path.endswith("/auth/customer/password/verify-otp"):
        return {"email": "a@test.com", "otp": "123456"}
    if path.endswith("/auth/customer/password/forgot/resend-otp"):
        return {"email": "a@test.com"}
    if path.endswith("/auth/customer/password/reset"):
        return {"resetToken": "x", "newPassword": "Password123!"}
    if path.endswith("/auth/vendor/register"):
        return {"displayName": "V", "email": "v@test.com", "password": "Password123!"}
    if path.endswith("/auth/vendor/login"):
        return {"email": "v@test.com", "password": "Password123!"}
    if path.endswith("/auth/vendor/token/refresh"):
        return {"refreshToken": "x"}
    if path.endswith("/auth/vendor/password/forgot"):
        return {"email": "v@test.com"}
    if path.endswith("/auth/vendor/password/verify-otp"):
        return {"email": "v@test.com", "otp": "123456"}
    if path.endswith("/auth/vendor/password/forgot/resend-otp"):
        return {"email": "v@test.com"}
    if path.endswith("/auth/vendor/password/reset"):
        return {"resetToken": "x", "newPassword": "Password123!"}
    if path.endswith("/auth/admin/login"):
        return {"email": "admin@test.com", "password": "Password123!"}
    if path.endswith("/auth/admin/login/verify-otp"):
        return {"email": "admin@test.com", "otp": "123456"}
    if path.endswith("/auth/admin/token/refresh"):
        return {"refreshToken": "x"}
    if path.endswith("/auth/admin/password/forgot"):
        return {"email": "admin@test.com"}
    if path.endswith("/auth/admin/password/verify-otp"):
        return {"email": "admin@test.com", "otp": "123456"}
    if path.endswith("/auth/admin/password/reset"):
        return {"resetToken": "x", "newPassword": "Password123!"}
    return {"dummy": "payload"}


@pytest.mark.parametrize("method,path", CASES)
def test_http_method_contract_rejects_with_client_error(client, method, path):
    request = getattr(client, method.lower())
    payload = _payload_for(path)
    if method in {"POST", "PUT", "PATCH"}:
        r = request(path, json=payload)
    else:
        r = request(path)
    assert 400 <= r.status_code < 500
