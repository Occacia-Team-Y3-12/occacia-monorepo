# from uuid import uuid4
# import pytest


# def test_create_persona_success(auth_client):
#     r = auth_client.post("/api/v1/personas/", json={
#         "name": "Sarah",
#         "relationship": "girlfriend",
#         "birthday": "2000-05-15T00:00:00Z",
#         "personality": "introverted, loves cozy things",
#         "preferences_json": ["hiking", "books", "coffee"],
#     })
#     assert r.status_code == 201
#     data = r.json()
#     assert data["name"] == "Sarah"
#     assert data["relationship"] == "girlfriend"
#     assert data["personality"] == "introverted, loves cozy things"
#     assert "persona_id" in data
#     assert data["persona_id"].startswith("PER-")


# def test_create_persona_minimal(auth_client):
#     r = auth_client.post("/api/v1/personas/", json={"name": "Mom"})
#     assert r.status_code == 201
#     assert r.json()["name"] == "Mom"


# def test_list_personas_empty(auth_client):
#     r = auth_client.get("/api/v1/personas/")
#     assert r.status_code == 200
#     assert r.json()["total"] == 0
#     assert r.json()["personas"] == []


# def test_list_personas_returns_own_only(auth_client, client):
#     # Create persona for first customer
#     auth_client.post("/api/v1/personas/", json={"name": "Sarah"})
#     auth_client.post("/api/v1/personas/", json={"name": "Mom"})

#     r = auth_client.get("/api/v1/personas/")
#     assert r.status_code == 200
#     assert r.json()["total"] == 2


# def test_get_persona_by_id(auth_client):
#     create_r = auth_client.post("/api/v1/personas/", json={
#         "name": "Sarah",
#         "relationship": "girlfriend",
#     })
#     persona_id = create_r.json()["persona_id"]

#     r = auth_client.get(f"/api/v1/personas/{persona_id}")
#     assert r.status_code == 200
#     assert r.json()["name"] == "Sarah"
#     assert r.json()["persona_id"] == persona_id


# def test_get_persona_not_found(auth_client):
#     r = auth_client.get("/api/v1/personas/PER-doesnotexist")
#     assert r.status_code == 404


# def test_delete_persona_success(auth_client):
#     create_r = auth_client.post("/api/v1/personas/", json={"name": "Sarah"})
#     persona_id = create_r.json()["persona_id"]

#     r = auth_client.delete(f"/api/v1/personas/{persona_id}")
#     assert r.status_code == 200
#     assert "deleted" in r.json()["message"].lower()

#     # Verify gone
#     get_r = auth_client.get(f"/api/v1/personas/{persona_id}")
#     assert get_r.status_code == 404


# def test_delete_persona_not_found(auth_client):
#     r = auth_client.delete("/api/v1/personas/PER-doesnotexist")
#     assert r.status_code == 404


# def test_personas_require_auth(client):
#     r = client.get("/api/v1/personas/")
#     assert r.status_code == 401

#     r = client.post("/api/v1/personas/", json={"name": "Sarah"})
#     assert r.status_code == 401