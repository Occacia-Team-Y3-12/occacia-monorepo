# ruff: noqa: S101

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
