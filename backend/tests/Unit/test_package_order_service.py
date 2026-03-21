# ruff: noqa: S101

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.package_order_service import PackageOrderService, event_planning_service


def test_confirm_package_order_returns_existing_event_package_order_without_creating_new_rows(monkeypatch):
    service = PackageOrderService()
    db = MagicMock()
    existing_order = SimpleNamespace(event_id="EVT-001", package_id="PKG-001", execution_request_id="EXE-001")
    monkeypatch.setattr(
        event_planning_service,
        "get_event_for_customer",
        MagicMock(return_value=SimpleNamespace(event_id="EVT-001", status="ACTIVE")),
    )

    service._get_order_by_event_and_package = MagicMock(return_value=existing_order)
    service._load_order_bundle = MagicMock(return_value=(existing_order, [], []))

    result = service.confirm_package_order(
        db,
        customer_id="CUS-001",
        event_id="EVT-001",
        package_id="PKG-001",
        idempotency_key="idempotency-key",
    )

    assert result == (existing_order, [], [])
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_confirm_package_order_rejects_idempotency_key_reused_for_different_order(monkeypatch):
    service = PackageOrderService()
    db = MagicMock()
    monkeypatch.setattr(
        event_planning_service,
        "get_event_for_customer",
        MagicMock(return_value=SimpleNamespace(event_id="EVT-001", status="ACTIVE")),
    )

    service._get_order_by_event_and_package = MagicMock(return_value=None)
    service._get_order_by_idempotency_key = MagicMock(
        return_value=SimpleNamespace(event_id="EVT-999", package_id="PKG-999")
    )

    with pytest.raises(HTTPException) as exc:
        service.confirm_package_order(
            db,
            customer_id="CUS-001",
            event_id="EVT-001",
            package_id="PKG-001",
            idempotency_key="idempotency-key",
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Idempotency key is already used for a different package order"


def test_get_tasks_by_ids_preserves_request_order():
    service = PackageOrderService()
    db = MagicMock()
    query = db.query.return_value
    filtered_query = query.filter.return_value
    filtered_query.all.return_value = [
        SimpleNamespace(task_id="TSK-2"),
        SimpleNamespace(task_id="TSK-1"),
    ]

    tasks = service._get_tasks_by_ids(db, task_ids=["TSK-1", "TSK-2"])

    assert [task.task_id for task in tasks] == ["TSK-1", "TSK-2"]


def test_reassign_rejected_task_updates_task_and_creates_next_attempt(monkeypatch):
    service = PackageOrderService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        event_planning_service,
        "get_event_for_customer",
        MagicMock(return_value=SimpleNamespace(event_id="EVT-001", status="ACTIVE")),
    )
    monkeypatch.setattr("app.services.package_order_service.now_utc", MagicMock(return_value=timestamp))

    task = SimpleNamespace(
        event_id="EVT-001",
        task_id="TSK-001",
        status="REJECTED",
        assigned_vendor_id="VEN-OLD",
        selected_offering_id="OFF-OLD",
        rejected_at="old",
        rejection_reason="busy",
        expires_at="expired",
        status_updated_at=None,
    )
    offering = SimpleNamespace(
        offering_id="OFF-NEW",
        vendor_id="VEN-NEW",
        is_active=True,
        is_available=True,
    )
    previous_request = SimpleNamespace(
        package_order_id="PKO-001",
        attempt_no=1,
    )

    task_query = MagicMock()
    task_query.filter.return_value.first.return_value = task

    recommendation_query = MagicMock()
    recommendation_query.filter.return_value.first.return_value = SimpleNamespace(offering_id="OFF-NEW")

    offering_query = MagicMock()
    offering_query.filter.return_value.first.return_value = offering

    request_query = MagicMock()
    request_query.filter.return_value.order_by.return_value.first.return_value = previous_request

    db.query.side_effect = [task_query, recommendation_query, offering_query, request_query]

    updated_task, new_request = service.reassign_rejected_task(
        db,
        customer_id="CUS-001",
        event_id="EVT-001",
        task_id="TSK-001",
        offering_id="OFF-NEW",
    )

    assert updated_task is task
    assert task.status == "PENDING"
    assert task.assigned_vendor_id == "VEN-NEW"
    assert task.selected_offering_id == "OFF-NEW"
    assert task.rejected_at is None
    assert task.rejection_reason is None
    assert task.expires_at is None
    assert task.status_updated_at is timestamp
    assert new_request.package_order_id == "PKO-001"
    assert new_request.task_id == "TSK-001"
    assert new_request.vendor_id == "VEN-NEW"
    assert new_request.offering_id == "OFF-NEW"
    assert new_request.status == "SENT"
    assert new_request.attempt_no == 2
    db.add.assert_any_call(task)
    db.add.assert_any_call(new_request)
    db.commit.assert_called_once()
    db.refresh.assert_any_call(task)
    db.refresh.assert_any_call(new_request)


def test_reassign_rejected_task_rejects_offering_outside_shortlist(monkeypatch):
    service = PackageOrderService()
    db = MagicMock()
    monkeypatch.setattr(
        event_planning_service,
        "get_event_for_customer",
        MagicMock(return_value=SimpleNamespace(event_id="EVT-001", status="ACTIVE")),
    )

    task_query = MagicMock()
    task_query.filter.return_value.first.return_value = SimpleNamespace(
        event_id="EVT-001",
        task_id="TSK-001",
        status="REJECTED",
        assigned_vendor_id="VEN-OLD",
    )
    recommendation_query = MagicMock()
    recommendation_query.filter.return_value.first.return_value = None
    db.query.side_effect = [task_query, recommendation_query]

    with pytest.raises(HTTPException) as exc:
        service.reassign_rejected_task(
            db,
            customer_id="CUS-001",
            event_id="EVT-001",
            task_id="TSK-001",
            offering_id="OFF-INVALID",
        )

    assert exc.value.status_code == 400
    assert "not in the shortlist" in exc.value.detail
    db.commit.assert_not_called()
