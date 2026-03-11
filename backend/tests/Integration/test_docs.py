def test_swagger_ui_available(client):
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_redoc_available(client):
    response = client.get("/api/redoc")
    assert response.status_code == 200
    assert "ReDoc" in response.text


def test_openapi_schema_available(client):
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()

    assert "openapi" in data
    assert "/api/v1/health" in data.get("paths", {})
