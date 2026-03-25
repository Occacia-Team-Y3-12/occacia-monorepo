from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.task import Task
from app.models.vendor import Vendor


def _create_vendor(*, approved: bool = True) -> Vendor:
    db = SessionLocal()
    vendor = Vendor(
        vendor_id=f"VEN-{uuid4().hex[:16]}",
        business_name="Task Vendor",
        display_name="Task Vendor",
        email=f"vendor-{uuid4().hex[:8]}@test.com",
        approval_status="APPROVED" if approved else "PENDING",
        is_verified=True,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    db.expunge(vendor)
    db.close()
    return vendor


def _create_task(*, vendor_id: str, status: str, name: str) -> Task:
    db = SessionLocal()
    task = Task(
        event_id=f"EVT-{uuid4().hex[:10]}",
        name=name,
        status=status,
        quantity=1,
        currency="LKR",
        assigned_vendor_id=vendor_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    db.expunge(task)
    db.close()
    return task


def _vendor_token(email: str) -> str:
    return create_access_token({"sub": email, "role": "VENDOR"})


def test_list_vendor_tasks_requires_auth(client):
    r = client.get("/api/v1/vendors/tasks")
    assert r.status_code == 401


def test_list_vendor_tasks_unapproved_vendor_blocked(client):
    vendor = _create_vendor(approved=False)
    token = _vendor_token(vendor.email)
    r = client.get("/api/v1/vendors/tasks", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_list_vendor_tasks_returns_only_default_statuses(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)

    _create_task(vendor_id=vendor.vendor_id, status="ASSIGNED", name="Assigned")
    _create_task(vendor_id=vendor.vendor_id, status="IN_PROGRESS", name="In Progress")
    _create_task(vendor_id=vendor.vendor_id, status="DONE", name="Done")
    _create_task(vendor_id=vendor.vendor_id, status="PENDING", name="Pending should be filtered")

    r = client.get("/api/v1/vendors/tasks", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    names = [item["name"] for item in body["items"]]
    assert "Assigned" in names
    assert "In Progress" in names
    assert "Done" in names
    assert "Pending should be filtered" not in names


@pytest.mark.parametrize("status", ["ASSIGNED", "IN_PROGRESS", "DONE"])
def test_list_vendor_tasks_status_filter(client, status):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    _create_task(vendor_id=vendor.vendor_id, status="ASSIGNED", name="A")
    _create_task(vendor_id=vendor.vendor_id, status="IN_PROGRESS", name="B")
    _create_task(vendor_id=vendor.vendor_id, status="DONE", name="C")

    r = client.get(
        "/api/v1/vendors/tasks",
        params={"status": status},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert all(item["status"] == status for item in r.json()["items"])


def test_get_vendor_task_not_owned_returns_404(client):
    vendor_a = _create_vendor(approved=True)
    vendor_b = _create_vendor(approved=True)
    token_b = _vendor_token(vendor_b.email)
    task_a = _create_task(vendor_id=vendor_a.vendor_id, status="ASSIGNED", name="A task")

    r = client.get(f"/api/v1/vendors/tasks/{task_a.task_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404


def test_get_vendor_task_success(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    task = _create_task(vendor_id=vendor.vendor_id, status="ASSIGNED", name="Owned task")

    r = client.get(f"/api/v1/vendors/tasks/{task.task_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["taskId"] == task.task_id


def test_update_vendor_task_transition_assigned_to_in_progress(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    task = _create_task(vendor_id=vendor.vendor_id, status="ASSIGNED", name="Transition task")

    r = client.put(
        f"/api/v1/vendors/tasks/{task.task_id}",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"


def test_update_vendor_task_invalid_transition_conflict(client):
    vendor = _create_vendor(approved=True)
    token = _vendor_token(vendor.email)
    task = _create_task(vendor_id=vendor.vendor_id, status="ASSIGNED", name="Bad transition task")

    r = client.put(
        f"/api/v1/vendors/tasks/{task.task_id}",
        json={"status": "DONE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 409

