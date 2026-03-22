def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "active"
    assert payload.get("system") == "Occacia Core"
    assert isinstance(payload.get("version"), str)
    assert isinstance(payload.get("uptimeSeconds"), int)
    assert payload["uptimeSeconds"] >= 0
