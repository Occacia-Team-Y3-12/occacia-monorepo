from __future__ import annotations

from app.core.security import create_access_token


def test_customer_calendar_connect_exchange_flow_integration(client, active_customer):
    access = create_access_token({"sub": active_customer.email})
    client.headers.update({"Authorization": f"Bearer {access}"})

    connect = client.post(
        "/api/v1/customers/calendar/connect",
        json={"provider": "google", "redirectUri": "https://app.occacia.com/oauth/callback"},
    )
    assert connect.status_code == 200
    payload = connect.json()
    assert payload["provider"] == "GOOGLE"
    assert "authorizationUrl" in payload

    exchange = client.post(
        "/api/v1/customers/calendar/exchange-code",
        json={
            "provider": "google",
            "code": "test-code",
            "state": payload["state"],
            "redirectUri": "https://app.occacia.com/oauth/callback",
        },
    )
    assert exchange.status_code == 200
    status_payload = exchange.json()
    assert status_payload["connected"] is True
    assert status_payload["provider"] == "GOOGLE"

    status = client.get("/api/v1/customers/calendar/status")
    assert status.status_code == 200
    assert status.json()["connected"] is True

    disconnect = client.delete("/api/v1/customers/calendar/disconnect")
    assert disconnect.status_code == 204
