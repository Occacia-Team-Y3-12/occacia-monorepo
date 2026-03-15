from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.core.config import settings


class GoogleCalendarService:
    _auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    _token_url = "https://oauth2.googleapis.com/token"  # noqa: S105
    _userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    _calendar_base_url = "https://www.googleapis.com/calendar/v3"

    def build_google_auth_url(self, *, state: str, redirect_uri: str | None) -> str:
        client_id = self._require_setting(settings.GOOGLE_CLIENT_ID, "GOOGLE_CLIENT_ID")
        resolved_redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        resolved_redirect_uri = self._require_setting(resolved_redirect_uri, "GOOGLE_REDIRECT_URI")
        scopes = self._require_setting(settings.GOOGLE_CALENDAR_SCOPES, "GOOGLE_CALENDAR_SCOPES")

        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": resolved_redirect_uri,
                "response_type": "code",
                "access_type": "offline",
                "prompt": "consent",
                "scope": scopes,
                "state": state,
                "include_granted_scopes": "true",
            }
        )
        return f"{self._auth_base_url}?{query}"

    def exchange_google_code(self, *, code: str, redirect_uri: str | None) -> dict[str, Any]:
        payload = {
            "code": code,
            "client_id": self._require_setting(settings.GOOGLE_CLIENT_ID, "GOOGLE_CLIENT_ID"),
            "client_secret": self._require_setting(
                settings.GOOGLE_CLIENT_SECRET,
                "GOOGLE_CLIENT_SECRET",
            ),
            "redirect_uri": self._require_setting(
                redirect_uri or settings.GOOGLE_REDIRECT_URI,
                "GOOGLE_REDIRECT_URI",
            ),
            "grant_type": "authorization_code",
        }
        return self._post_token(payload)

    def refresh_google_access_token(self, *, refresh_token: str) -> dict[str, Any]:
        payload = {
            "client_id": self._require_setting(settings.GOOGLE_CLIENT_ID, "GOOGLE_CLIENT_ID"),
            "client_secret": self._require_setting(
                settings.GOOGLE_CLIENT_SECRET,
                "GOOGLE_CLIENT_SECRET",
            ),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        return self._post_token(payload)

    def get_google_account_profile(self, *, access_token: str) -> dict[str, str | None]:
        user_info = self._get(
            self._userinfo_url,
            access_token=access_token,
        )
        calendar_list = self._get(
            f"{self._calendar_base_url}/users/me/calendarList/primary",
            access_token=access_token,
        )
        return {
            "email": user_info.get("email"),
            "calendar_id": calendar_list.get("id"),
        }

    def create_google_event(
        self,
        *,
        access_token: str,
        calendar_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._post_json(
            f"{self._calendar_base_url}/calendars/{calendar_id}/events",
            access_token=access_token,
            payload=payload,
        )

    def update_google_event(
        self,
        *,
        access_token: str,
        calendar_id: str,
        event_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._put_json(
            f"{self._calendar_base_url}/calendars/{calendar_id}/events/{event_id}",
            access_token=access_token,
            payload=payload,
        )

    def delete_google_event(self, *, access_token: str, calendar_id: str, event_id: str) -> None:
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client(timeout=15.0) as client:
            response = client.delete(
                f"{self._calendar_base_url}/calendars/{calendar_id}/events/{event_id}",
                headers=headers,
            )
        if response.status_code not in {204, 404}:
            self._raise_google_error(response)

    def build_event_payload(
        self,
        *,
        event,
        description: str,
        reminder_overrides: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "summary": event.title,
            "description": description,
            "location": event.location_text,
            "reminders": {"useDefault": False, "overrides": reminder_overrides},
        }

        if event.is_all_day:
            start_date = event.start_at.astimezone(UTC).date().isoformat()
            end_reference = (
                event.end_at.astimezone(UTC)
                if event.end_at
                else event.start_at + timedelta(days=1)
            )
            end_date = end_reference.astimezone(UTC).date().isoformat()
            payload["start"] = {"date": start_date}
            payload["end"] = {"date": end_date}
        else:
            payload["start"] = {"dateTime": event.start_at.isoformat(), "timeZone": event.timezone}
            payload["end"] = {
                "dateTime": (event.end_at or (event.start_at + timedelta(hours=1))).isoformat(),
                "timeZone": event.timezone,
            }

        if event.recurrence_rule:
            payload["recurrence"] = [f"RRULE:{event.recurrence_rule}"]

        return payload

    def _post_token(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(self._token_url, data=payload)
        if response.status_code >= 400:
            self._raise_google_error(response)
        return response.json()

    def _get(self, url: str, *, access_token: str) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code >= 400:
            self._raise_google_error(response)
        return response.json()

    def _post_json(self, url: str, *, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 400:
            self._raise_google_error(response)
        return response.json()

    def _put_json(self, url: str, *, access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15.0) as client:
            response = client.put(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 400:
            self._raise_google_error(response)
        return response.json()

    def parse_expiry(self, token_payload: dict[str, Any]) -> datetime | None:
        expires_in = token_payload.get("expires_in")
        if expires_in is None:
            return None
        return datetime.now(UTC) + timedelta(seconds=int(expires_in))

    def _raise_google_error(self, response: httpx.Response) -> None:
        detail = "Google Calendar request failed"
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                detail = error.get("message") or detail
            elif isinstance(error, str):
                detail = error
        raise HTTPException(status_code=502, detail=detail)

    def _require_setting(self, value: str | None, name: str) -> str:
        if not value:
            raise HTTPException(status_code=500, detail=f"{name} is not configured")
        return value


google_calendar_service = GoogleCalendarService()
