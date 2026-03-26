from __future__ import annotations


def test_event_chat_requires_auth(client):
    r = client.post("/api/v1/customers/events/EVT-UNKNOWN/chat", json={"content": "hello"})
    assert r.status_code == 401
