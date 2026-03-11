# ruff: noqa: S101

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.event_planning_service import EventPlanningService


def test_whenServiceParsesYearlyRecurrence_parseRrule_success():
    service = EventPlanningService()

    parsed = service._parse_rrule("FREQ=YEARLY;INTERVAL=1;COUNT=3")

    assert parsed["FREQ"] == "YEARLY"
    assert parsed["INTERVAL"] == 1
    assert parsed["COUNT"] == 3


def test_whenServiceParsesInvalidRecurrence_parseRrule_failsWithException():
    service = EventPlanningService()

    with pytest.raises(HTTPException) as exc:
        service._parse_rrule("FREQ=INVALID;INTERVAL=1")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Unsupported recurrence frequency"


def test_whenServiceParsesReminderOffset_parseDuration_success():
    service = EventPlanningService()

    duration = service._parse_duration("P7D")

    assert duration.days == 7
    assert duration.seconds == 0


def test_whenServiceParsesInvalidReminderOffset_parseDuration_failsWithException():
    service = EventPlanningService()

    with pytest.raises(HTTPException) as exc:
        service._parse_duration("7D")

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid reminder offset: 7D"


def test_whenRecurringEventHasFutureOccurrences_generateOccurrences_success():
    service = EventPlanningService()
    event = SimpleNamespace(
        event_id="EVT-001",
        start_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 6, 10, 15, 0, tzinfo=timezone.utc),
        recurrence_rule="FREQ=YEARLY;INTERVAL=1;COUNT=3",
        recurrence_until=None,
        recurrence_count=None,
    )

    occurrences = service._generate_occurrences(
        event,
        from_dt=datetime(2026, 1, 1, tzinfo=timezone.utc),
        count=2,
    )

    assert len(occurrences) == 2
    assert occurrences[0]["occurrenceId"] == "EVT-001:1"
    assert occurrences[0]["startAt"] == datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    assert occurrences[1]["startAt"] == datetime(2027, 6, 10, 12, 0, tzinfo=timezone.utc)


def test_whenCustomerConfirmsWithoutTasks_confirmTasks_failsWithException():
    service = EventPlanningService()
    db = MagicMock()
    event = SimpleNamespace(
        status="DRAFT",
        confirmed_at=None,
        reminders_enabled=False,
        start_at=None,
        calendar_sync_state="DISABLED",
        calendar_sync_provider=None,
        calendar_last_sync_status=None,
        calendar_last_sync_at=None,
        external_calendar_event_id=None,
    )
    service.get_event_for_customer = MagicMock(return_value=event)
    service.list_tasks = MagicMock(return_value=[])

    with pytest.raises(HTTPException) as exc:
        service.confirm_tasks(
            db,
            customer_id="CUS-001",
            event_id="EVT-001",
            task_ids=None,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Add at least 1 task"
