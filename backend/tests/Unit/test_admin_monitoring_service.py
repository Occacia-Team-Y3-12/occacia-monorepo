# ruff: noqa: S101

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.admin_service import AdminService


def test_create_internal_note_persists_note_fields():
    service = AdminService()
    db = MagicMock()

    note = service.create_internal_note(
        db,
        admin_id="ADM-001",
        package_order_id="EXE-001",
        event_id="EVT-001",
        task_id="TSK-001",
        vendor_id="VEN-001",
        action_type="NOTE_ONLY",
        note="Investigating vendor issue",
    )

    assert note.admin_id == "ADM-001"
    assert note.package_order_id == "EXE-001"
    assert note.event_id == "EVT-001"
    assert note.task_id == "TSK-001"
    assert note.vendor_id == "VEN-001"
    assert note.action_type == "NOTE_ONLY"
    assert note.note == "Investigating vendor issue"
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(note)


def test_apply_task_support_action_unassign_vendor_clears_assignment_and_adds_note(monkeypatch):
    service = AdminService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.admin_service.now_utc", MagicMock(return_value=timestamp))

    task = SimpleNamespace(
        task_id="TSK-001",
        event_id="EVT-001",
        assigned_vendor_id="VEN-001",
        selected_offering_id="OFF-001",
        status="PENDING",
        rejected_at="old",
        rejection_reason="busy",
        expires_at=timestamp - timedelta(minutes=1),
        status_updated_at=None,
    )
    service.get_task = MagicMock(return_value=task)
    service._get_latest_package_order_id = MagicMock(return_value="EXE-001")

    updated_task = service.apply_task_support_action(
        db,
        admin_id="ADM-001",
        task_id="TSK-001",
        action="UNASSIGN_VENDOR",
        note="Removed assignment for review",
    )

    assert updated_task is task
    assert task.assigned_vendor_id is None
    assert task.selected_offering_id is None
    assert task.status == "PENDING"
    assert task.rejected_at is None
    assert task.rejection_reason is None
    assert task.expires_at is None
    assert task.status_updated_at is timestamp
    assert db.commit.call_count == 1
    assert db.refresh.call_args_list[-1].args == (task,)
    support_note = db.add.call_args_list[0].args[0]
    assert support_note.admin_id == "ADM-001"
    assert support_note.package_order_id == "EXE-001"
    assert support_note.task_id == "TSK-001"
    assert support_note.action_type == "UNASSIGN_VENDOR"


def test_apply_task_support_action_extend_expiry_requires_future_datetime(monkeypatch):
    service = AdminService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.admin_service.now_utc", MagicMock(return_value=timestamp))
    task = SimpleNamespace(task_id="TSK-001", status="PENDING")
    service.get_task = MagicMock(return_value=task)

    with pytest.raises(HTTPException) as exc:
        service.apply_task_support_action(
            db,
            admin_id="ADM-001",
            task_id="TSK-001",
            action="EXTEND_EXPIRY",
            expires_at=timestamp,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "expiresAt must be in the future"
    db.rollback.assert_called_once()


def test_apply_task_support_action_override_terminal_task_is_blocked(monkeypatch):
    service = AdminService()
    db = MagicMock()
    monkeypatch.setattr(
        "app.services.admin_service.now_utc",
        MagicMock(return_value=datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc)),
    )
    task = SimpleNamespace(
        task_id="TSK-001",
        status="DONE",
        assigned_vendor_id="VEN-001",
        rejected_at=None,
        rejection_reason=None,
        expires_at=None,
    )
    service.get_task = MagicMock(return_value=task)

    with pytest.raises(HTTPException) as exc:
        service.apply_task_support_action(
            db,
            admin_id="ADM-001",
            task_id="TSK-001",
            action="OVERRIDE_STATUS",
            status_value="ASSIGNED",
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "Terminal tasks cannot be overridden"


def test_apply_task_support_action_reassign_vendor_creates_new_request(monkeypatch):
    service = AdminService()
    db = MagicMock()
    timestamp = datetime(2026, 3, 21, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.admin_service.now_utc", MagicMock(return_value=timestamp))

    task = SimpleNamespace(
        task_id="TSK-001",
        event_id="EVT-001",
        assigned_vendor_id="VEN-OLD",
        selected_offering_id="OFF-OLD",
        status="REJECTED",
        rejected_at=timestamp,
        rejection_reason="busy",
        expires_at=timestamp,
        status_updated_at=None,
        currency="LKR",
        needs_vendor="cake",
    )
    latest_request = SimpleNamespace(package_order_id="EXE-001", attempt_no=1)
    vendor = SimpleNamespace(vendor_id="VEN-NEW")
    offering = SimpleNamespace(offering_id="OFF-NEW")

    service.get_task = MagicMock(return_value=task)
    service._resolve_reassignment_offering = MagicMock(return_value=offering)
    service._cancel_open_requests = MagicMock()

    vendor_query = MagicMock()
    vendor_query.filter.return_value.first.return_value = vendor
    request_query = MagicMock()
    request_query.filter.return_value.order_by.return_value.first.return_value = latest_request
    db.query.side_effect = [vendor_query, request_query]

    updated_task = service.apply_task_support_action(
        db,
        admin_id="ADM-001",
        task_id="TSK-001",
        action="REASSIGN_VENDOR",
        assigned_vendor_id="VEN-NEW",
    )

    assert updated_task is task
    assert task.assigned_vendor_id == "VEN-NEW"
    assert task.selected_offering_id == "OFF-NEW"
    assert task.status == "PENDING"
    assert task.rejected_at is None
    assert task.rejection_reason is None
    assert task.expires_at is None
    new_request = db.add.call_args_list[0].args[0]
    assert new_request.package_order_id == "EXE-001"
    assert new_request.vendor_id == "VEN-NEW"
    assert new_request.offering_id == "OFF-NEW"
    assert new_request.attempt_no == 2
