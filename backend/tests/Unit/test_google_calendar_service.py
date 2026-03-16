# ruff: noqa: S101

from datetime import UTC, datetime
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from app.services.google_calendar_service import GoogleCalendarService


def test_whenBuildingGoogleAuthUrl_buildGoogleAuthUrl_success():
    service = GoogleCalendarService()

    auth_url = service.build_google_auth_url(
        state="STATE-123",
        redirect_uri="https://app.occacia.com/oauth/callback",
    )

    parsed = urlparse(auth_url)
    query = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.google.com"
    assert query["state"] == ["STATE-123"]
    assert query["redirect_uri"] == ["https://app.occacia.com/oauth/callback"]
    assert query["response_type"] == ["code"]


def test_whenBuildingGoogleEventPayload_buildEventPayload_success():
    service = GoogleCalendarService()
    event = SimpleNamespace(
        title="Birthday Dinner",
        description=None,
        location_text="Colombo",
        start_at=datetime(2026, 8, 1, 18, 0, tzinfo=UTC),
        end_at=datetime(2026, 8, 1, 21, 0, tzinfo=UTC),
        timezone="Asia/Colombo",
        is_all_day=False,
        recurrence_rule="FREQ=YEARLY;INTERVAL=1",
    )

    payload = service.build_event_payload(
        event=event,
        description="Birthday Dinner (Birthday)",
        reminder_overrides=[{"method": "popup", "minutes": 1440}],
    )

    assert payload["summary"] == "Birthday Dinner"
    assert payload["location"] == "Colombo"
    assert payload["start"]["timeZone"] == "Asia/Colombo"
    assert payload["recurrence"] == ["RRULE:FREQ=YEARLY;INTERVAL=1"]
    assert payload["reminders"]["overrides"][0]["minutes"] == 1440
