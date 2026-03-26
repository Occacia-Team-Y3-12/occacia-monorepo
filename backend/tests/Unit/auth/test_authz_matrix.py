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

AUTH_REQUIRED_CASES = [
    ("GET", "/api/v1/customers/me"),
    ("PUT", "/api/v1/customers/me"),
    ("GET", "/api/v1/customers/events"),
    ("POST", "/api/v1/customers/events"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/personas"),
    ("DELETE", f"/api/v1/customers/events/{EVENT_ID}"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/chat"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/messages"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/summarize"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/tasks"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/tasks"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}"),
    ("DELETE", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/tasks/confirm"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/reassign"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/recommendations"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/tasks/{TASK_ID}/recommendations"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/packages"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/packages"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}"),
    ("PUT", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}"),
    ("DELETE", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}"),
    ("POST", f"/api/v1/customers/events/{EVENT_ID}/packages/{PACKAGE_ID}/confirm"),
    ("GET", f"/api/v1/customers/events/{EVENT_ID}/package-orders"),
    ("GET", "/api/v1/customers/package-orders"),
    ("GET", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}"),
    ("PUT", f"/api/v1/customers/package-orders/{PACKAGE_ORDER_ID}/cancel"),
    ("GET", "/api/v1/customers/inquiries"),
    ("POST", "/api/v1/customers/inquiries"),
    ("GET", f"/api/v1/customers/inquiries/{INQUIRY_ID}"),
    ("GET", "/api/v1/customers/calendar/providers"),
    ("POST", "/api/v1/customers/calendar/connect"),
    ("POST", "/api/v1/customers/calendar/exchange-code"),
    ("GET", "/api/v1/customers/calendar/status"),
    ("DELETE", "/api/v1/customers/calendar/disconnect"),
    ("GET", "/api/v1/vendors/me"),
    ("PUT", "/api/v1/vendors/me"),
    ("GET", "/api/v1/vendors/fulfillment-requests"),
    ("GET", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}"),
    ("POST", f"/api/v1/vendors/fulfillment-requests/{FULFILLMENT_REQUEST_ID}/response"),
    ("GET", "/api/v1/vendors/tasks"),
    ("GET", f"/api/v1/vendors/tasks/{TASK_ID}"),
    ("PUT", f"/api/v1/vendors/tasks/{TASK_ID}"),
    ("GET", "/api/v1/vendors/me/packages"),
    ("POST", "/api/v1/vendors/me/packages"),
    ("PUT", "/api/v1/vendors/me/packages/1"),
    ("DELETE", "/api/v1/vendors/me/packages/1"),
    ("GET", "/api/v1/vendors/offerings"),
    ("POST", "/api/v1/vendors/offerings"),
    ("GET", f"/api/v1/vendors/offerings/{OFFERING_ID}"),
    ("PUT", f"/api/v1/vendors/offerings/{OFFERING_ID}"),
    ("DELETE", f"/api/v1/vendors/offerings/{OFFERING_ID}"),
    ("GET", "/api/v1/vendors/inquiries"),
    ("POST", "/api/v1/vendors/inquiries"),
    ("GET", f"/api/v1/vendors/inquiries/{INQUIRY_ID}"),
    ("GET", "/api/v1/admin/me"),
    ("GET", "/api/v1/admin/vendors"),
    ("GET", f"/api/v1/admin/vendors/{VENDOR_ID}"),
    ("PUT", f"/api/v1/admin/vendors/{VENDOR_ID}/status"),
    ("POST", f"/api/v1/admin/vendors/{VENDOR_ID}/approve"),
    ("POST", f"/api/v1/admin/vendors/{VENDOR_ID}/reject"),
    ("GET", "/api/v1/admin/vendors/stats/pending"),
    ("GET", "/api/v1/admin/customers"),
    ("GET", f"/api/v1/admin/customers/{CUSTOMER_ID}"),
    ("PUT", f"/api/v1/admin/customers/{CUSTOMER_ID}/status"),
    ("GET", "/api/v1/admin/organizations"),
    ("GET", f"/api/v1/admin/organizations/{ORG_ID}"),
    ("DELETE", f"/api/v1/admin/organizations/{ORG_ID}"),
    ("PUT", f"/api/v1/admin/organizations/{ORG_ID}/status"),
    ("GET", "/api/v1/admin/inquiries"),
    ("GET", f"/api/v1/admin/inquiries/{INQUIRY_ID}"),
    ("PUT", f"/api/v1/admin/inquiries/{INQUIRY_ID}"),
    ("GET", "/api/v1/admin/internal-notes"),
    ("POST", "/api/v1/admin/internal-notes"),
    ("GET", "/api/v1/admin/package-orders"),
    ("GET", f"/api/v1/admin/package-orders/{PACKAGE_ORDER_ID}"),
    ("GET", "/api/v1/admin/tasks"),
    ("GET", f"/api/v1/admin/tasks/{TASK_ID}"),
    ("PATCH", f"/api/v1/admin/tasks/{TASK_ID}"),
    ("GET", f"/api/v1/admin/tasks/{TASK_ID}/fulfillment-requests"),
    ("GET", "/api/v1/admin/dashboard"),
]


def payload_for(method: str, path: str):
    if method in {"POST", "PUT", "PATCH"}:
        if path.endswith("/customers/me"):
            return {"fullName": "Test User"}
        if "/customers/events" in path and path.endswith("/personas"):
            return {"personaIds": [PERSONA_ID]}
        if path.endswith("/customers/events"):
            return {"eventType": "BIRTHDAY", "title": "Test Event"}
        if "/customers/events" in path and path.endswith("/chat"):
            return {"content": "Hello"}
        if "/customers/events" in path and path.endswith("/tasks"):
            return {"name": "Task Name"}
        if "/tasks/confirm" in path:
            return {}
        if path.endswith("/reassign"):
            return {"offeringId": OFFERING_ID}
        if "/customers/events" in path and path.endswith("/packages"):
            return {"items": []}
        if "/customers/events" in path and path.endswith("/packages/" + PACKAGE_ID):
            return {"items": []}
        if path.endswith("/packages/" + PACKAGE_ID + "/confirm"):
            return {}
        if "/customers/package-orders" in path and path.endswith("/cancel"):
            return {}
        if path.endswith("/customers/inquiries"):
            return {"message": "Need help"}
        if path.endswith("/customers/calendar/connect"):
            return {"provider": "GOOGLE", "redirectUri": "https://example.com/callback"}
        if path.endswith("/customers/calendar/exchange-code"):
            return {"provider": "GOOGLE", "code": "code", "redirectUri": "https://example.com/callback"}
        if path.endswith("/vendors/me"):
            return {"displayName": "Vendor Name"}
        if path.endswith("/vendors/fulfillment-requests/" + FULFILLMENT_REQUEST_ID + "/response"):
            return {"decision": "ACCEPT"}
        if "/vendors/tasks/" in path and method == "PUT":
            return {"status": "IN_PROGRESS"}
        if path.endswith("/vendors/me/packages"):
            return {"name": "Package"}
        if path.endswith("/vendors/me/packages/1"):
            return {"name": "Updated Package"}
        if path.endswith("/vendors/offerings"):
            return {"name": "Offering", "category": "FOOD", "price": 100, "currency": "LKR"}
        if "/vendors/offerings/" in path and method == "PUT":
            return {"name": "Updated Offering"}
        if path.endswith("/vendors/inquiries"):
            return {"message": "Vendor inquiry"}
        if "/admin/vendors/" in path and path.endswith("/status"):
            return {"status": "ACTIVE"}
        if "/admin/vendors/" in path and path.endswith("/reject"):
            return {"reason": "Missing docs"}
        if "/admin/customers/" in path and path.endswith("/status"):
            return {"status": "ACTIVE"}
        if "/admin/organizations/" in path and path.endswith("/status"):
            return {"status": "ACTIVE"}
        if "/admin/inquiries/" in path and method == "PUT":
            return {"status": "IN_PROGRESS"}
        if path.endswith("/admin/internal-notes"):
            return {"actionType": "NOTE_ONLY", "note": "Auth required"}
        if "/admin/tasks/" in path and method == "PATCH":
            return {"action": "UNLOCK_EDITING"}
    return None


@pytest.mark.parametrize("method,path", AUTH_REQUIRED_CASES)
def test_auth_required_matrix(client, method, path):
    request = getattr(client, method.lower())
    payload = payload_for(method, path)
    headers = {}
    if path.endswith("/packages/" + PACKAGE_ID + "/confirm"):
        headers["Idempotency-Key"] = str(uuid.uuid4())
    if payload is None:
        r = request(path, headers=headers)
    else:
        r = request(path, json=payload, headers=headers)
    assert r.status_code in (401, 403)
