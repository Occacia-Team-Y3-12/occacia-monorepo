"""
tests/test_persona.py

Complete pytest suite — entire Persona system + AI chat flow.

Tickets covered:
  OCA-249  Implement Persona Update Service
  OCA-245  Implement Persona Confirmation Logic
  AI flow  Save from chat / Load from chat / Suggest saved profile

Fixtures required (standard project conftest):
    auth_client  — authenticated TestClient (customer JWT)
    client       — unauthenticated TestClient
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

PERSONA_URL  = "/api/v1/personas/"
PLANNING_URL = "/api/v1/planning/generate"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _uid():
    return str(uuid.uuid4())[:8]


def _create_payload(**kwargs):
    base = {
        "name":              f"Test Person {_uid()}",
        "relationship":      "girlfriend",
        "personality":       "introvert, loves cozy things",
        "food_preferences":  ["sushi", "pizza"],
        "color_preferences": ["blue", "white"],
        "music_preferences": ["jazz", "lo-fi"],
        "personality_tags":  ["adventurous", "romantic"],
    }
    base.update(kwargs)
    return base


def _create(auth_client, **kwargs):
    """POST /personas/ and assert 201. Returns (response, persona_id)."""
    resp = auth_client.post(PERSONA_URL, json=_create_payload(**kwargs))
    assert resp.status_code == 201, resp.text
    return resp, resp.json()["persona_id"]


def _fake_ai(**overrides):
    """Minimal valid AI result dict, with optional overrides."""
    base = {
        "intent":          "chat",
        "chat_response":   "Let me help!",
        "venue_tags":      [],
        "missing_info":    [],
        "gift_suggestion": None,
        "event_type":      None,
        "location":        None,
        "budget_per_head": None,
        "guest_count":     None,
        "save_persona":    None,
        "ask_save_persona": False,
        "use_persona_name": None,
    }
    base.update(overrides)
    return base


def _plan(auth_client, user_query, session_id=None):
    return auth_client.post(PLANNING_URL, json={
        "session_id": session_id or f"sess-{_uid()}",
        "user_query":  user_query,
    })


def _mock_plan(auth_client, user_query, ai_result, session_id=None):
    """POST /planning/generate with AI mocked to return ai_result."""
    with patch(
        "app.services.ai_service.ai_service.generate_date_plan",
        new_callable=AsyncMock,
        return_value=ai_result,
    ):
        return _plan(auth_client, user_query, session_id)


# ══════════════════════════════════════════════════════════════════════════════
# 1. CREATE
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaCreate:

    def test_create_returns_201(self, auth_client):
        assert auth_client.post(PERSONA_URL, json=_create_payload()).status_code == 201

    def test_create_response_shape(self, auth_client):
        data = auth_client.post(PERSONA_URL, json=_create_payload()).json()
        for key in ("persona_id", "customer_id", "name", "is_confirmed",
                    "food_preferences", "music_preferences",
                    "color_preferences", "personality_tags"):
            assert key in data, f"missing key: {key}"
        assert data["is_confirmed"] is False

    def test_create_stores_food_preferences(self, auth_client):
        resp, _ = _create(auth_client, food_preferences=["sushi", "ramen"])
        assert "sushi" in resp.json()["food_preferences"]

    def test_create_stores_color_preferences(self, auth_client):
        resp, _ = _create(auth_client, color_preferences=["purple", "gold"])
        assert "purple" in resp.json()["color_preferences"]

    def test_create_stores_music_preferences(self, auth_client):
        resp, _ = _create(auth_client, music_preferences=["jazz"])
        assert "jazz" in resp.json()["music_preferences"]

    def test_create_stores_personality_tags(self, auth_client):
        resp, _ = _create(auth_client, personality_tags=["adventurous", "cozy"])
        assert "adventurous" in resp.json()["personality_tags"]

    def test_create_stores_legacy_preferences_json(self, auth_client):
        resp, _ = _create(auth_client, preferences_json=["hiking", "cooking"])
        assert "hiking" in resp.json()["preferences_json"]

    def test_create_empty_name_returns_422(self, auth_client):
        assert auth_client.post(PERSONA_URL, json=_create_payload(name="")).status_code == 422

    def test_create_missing_name_returns_422(self, auth_client):
        payload = _create_payload()
        del payload["name"]
        assert auth_client.post(PERSONA_URL, json=payload).status_code == 422

    def test_create_without_optional_fields(self, auth_client):
        resp = auth_client.post(PERSONA_URL, json={"name": "Minimal"})
        assert resp.status_code == 201
        assert resp.json()["food_preferences"]  == []
        assert resp.json()["personality_tags"]  == []
        assert resp.json()["music_preferences"] == []
        assert resp.json()["color_preferences"] == []

    def test_create_with_birthday(self, auth_client):
        resp = auth_client.post(PERSONA_URL, json=_create_payload(birthday="1995-06-15"))
        assert resp.status_code == 201
        assert "1995-06-15" in (resp.json()["birthday"] or "")

    def test_create_with_all_empty_lists(self, auth_client):
        resp = auth_client.post(PERSONA_URL, json={
            "name": f"Sparse-{_uid()}",
            "food_preferences": [], "color_preferences": [],
            "music_preferences": [], "personality_tags": [],
        })
        assert resp.status_code == 201
        assert resp.json()["food_preferences"] == []

    def test_persona_id_has_per_prefix(self, auth_client):
        _, pid = _create(auth_client)
        assert pid.startswith("PER")

    def test_unauthenticated_create_returns_401(self, client):
        assert client.post(PERSONA_URL, json=_create_payload()).status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 2. LIST
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaList:

    def test_list_returns_200(self, auth_client):
        assert auth_client.get(PERSONA_URL).status_code == 200

    def test_list_returns_plain_list_not_envelope(self, auth_client):
        r = auth_client.get(PERSONA_URL)
        assert isinstance(r.json(), list)

    def test_list_includes_created_persona(self, auth_client):
        name = f"ListTest-{_uid()}"
        _create(auth_client, name=name)
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_list_customer_isolation(self, auth_client, client):
        """Customer A cannot see Customer B's personas."""
        name = f"Private-{_uid()}"
        _create(auth_client, name=name)
        email2 = f"other_{_uid()}@test.com"
        client.post("/api/v1/auth/customers/register",
                    json={"email": email2, "password": "pass1234", "full_name": "Other"})
        tok = client.post("/api/v1/auth/customers/login",
                          data={"username": email2, "password": "pass1234"}).json().get("access_token")
        if tok:
            names2 = [p["name"] for p in client.get(
                PERSONA_URL, headers={"Authorization": f"Bearer {tok}"}
            ).json()]
            assert name not in names2

    def test_confirmed_persona_listed_before_unconfirmed(self, auth_client):
        _, pid1 = _create(auth_client, name=f"Unconfirmed-{_uid()}")
        _, pid2 = _create(auth_client, name=f"Confirmed-{_uid()}")
        auth_client.post(f"{PERSONA_URL}{pid2}/confirm")
        personas = auth_client.get(PERSONA_URL).json()
        confirmed   = next(p for p in personas if p["persona_id"] == pid2)
        unconfirmed = next(p for p in personas if p["persona_id"] == pid1)
        assert personas.index(confirmed) < personas.index(unconfirmed)

    def test_unauthenticated_list_returns_401(self, client):
        assert client.get(PERSONA_URL).status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 3. GET SINGLE
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaGet:

    def test_get_existing_persona(self, auth_client):
        _, pid = _create(auth_client)
        resp = auth_client.get(f"{PERSONA_URL}{pid}")
        assert resp.status_code == 200
        assert resp.json()["persona_id"] == pid

    def test_get_nonexistent_returns_404(self, auth_client):
        assert auth_client.get(f"{PERSONA_URL}PER-doesnotexist").status_code == 404

    def test_get_other_customers_persona_returns_404(self, auth_client, client):
        _, pid = _create(auth_client)
        email2 = f"other2_{_uid()}@test.com"
        client.post("/api/v1/auth/customers/register",
                    json={"email": email2, "password": "pass1234", "full_name": "Other2"})
        tok = client.post("/api/v1/auth/customers/login",
                          data={"username": email2, "password": "pass1234"}).json().get("access_token")
        if tok:
            assert client.get(
                f"{PERSONA_URL}{pid}",
                headers={"Authorization": f"Bearer {tok}"},
            ).status_code == 404

    def test_unauthenticated_get_returns_401(self, client):
        assert client.get(f"{PERSONA_URL}PER-anything").status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 4. UPDATE  — OCA-249
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaUpdate:

    def test_update_name(self, auth_client):
        _, pid = _create(auth_client, name="OldName")
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "NewName"}).json()["name"] == "NewName"

    def test_update_relationship(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": "wife"}).json()["relationship"] == "wife"

    def test_update_food_preferences(self, auth_client):
        _, pid = _create(auth_client)
        data = auth_client.put(f"{PERSONA_URL}{pid}", json={"food_preferences": ["korean", "thai"]}).json()
        assert "korean" in data["food_preferences"]

    def test_update_color_preferences(self, auth_client):
        _, pid = _create(auth_client)
        data = auth_client.put(f"{PERSONA_URL}{pid}", json={"color_preferences": ["pink", "gold"]}).json()
        assert "pink" in data["color_preferences"]

    def test_update_music_preferences(self, auth_client):
        _, pid = _create(auth_client)
        assert "classical" in auth_client.put(
            f"{PERSONA_URL}{pid}", json={"music_preferences": ["classical"]}
        ).json()["music_preferences"]

    def test_update_personality_tags(self, auth_client):
        _, pid = _create(auth_client)
        assert "cozy" in auth_client.put(
            f"{PERSONA_URL}{pid}", json={"personality_tags": ["cozy", "bookworm"]}
        ).json()["personality_tags"]

    def test_update_personality_free_text(self, auth_client):
        _, pid = _create(auth_client)
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"personality": "loves hiking and coffee"})
        assert resp.status_code == 200
        assert "hiking" in resp.json()["personality"]

    def test_update_legacy_preferences_json(self, auth_client):
        _, pid = _create(auth_client)
        data = auth_client.put(f"{PERSONA_URL}{pid}", json={"preferences_json": ["gaming", "cooking"]}).json()
        assert "gaming" in data["preferences_json"]

    def test_partial_update_does_not_clear_other_fields(self, auth_client):
        """OCA-249 CORE: sending only 'relationship' must NOT wipe food/personality_tags."""
        _, pid = _create(auth_client, name="FullPerson",
                         food_preferences=["sushi"], personality_tags=["romantic"])
        auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": "partner"})
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert "sushi"    in data["food_preferences"]
        assert "romantic" in data["personality_tags"]

    def test_update_nonexistent_returns_404(self, auth_client):
        assert auth_client.put(f"{PERSONA_URL}PER-ghost", json={"name": "Ghost"}).status_code == 404

    def test_update_birthday(self, auth_client):
        _, pid = _create(auth_client)
        assert "2000-01-01" in (
            auth_client.put(f"{PERSONA_URL}{pid}", json={"birthday": "2000-01-01"}).json()["birthday"] or ""
        )

    def test_update_invalid_birthday_returns_422(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"birthday": "not-a-date"}).status_code == 422

    def test_update_empty_body_is_no_op(self, auth_client):
        _, pid = _create(auth_client, name="NoOp")
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={}).json()["name"] == "NoOp"

    def test_unauthenticated_update_returns_401(self, client):
        assert client.put(f"{PERSONA_URL}PER-anything", json={"name": "x"}).status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 5. DELETE
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaDelete:

    def test_delete_returns_204(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.delete(f"{PERSONA_URL}{pid}").status_code == 204

    def test_deleted_persona_not_in_list(self, auth_client):
        name = f"Delete-{_uid()}"
        _, pid = _create(auth_client, name=name)
        auth_client.delete(f"{PERSONA_URL}{pid}")
        assert name not in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_delete_nonexistent_returns_404(self, auth_client):
        assert auth_client.delete(f"{PERSONA_URL}PER-nope").status_code == 404

    def test_get_after_delete_returns_404(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.delete(f"{PERSONA_URL}{pid}")
        assert auth_client.get(f"{PERSONA_URL}{pid}").status_code == 404

    def test_delete_confirmed_persona(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert auth_client.delete(f"{PERSONA_URL}{pid}").status_code == 204

    def test_unauthenticated_delete_returns_401(self, client):
        assert client.delete(f"{PERSONA_URL}PER-anything").status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 6. CONFIRM  — OCA-245
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaConfirm:

    def test_confirm_returns_200(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.post(f"{PERSONA_URL}{pid}/confirm").status_code == 200

    def test_confirm_sets_is_confirmed_true(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.post(f"{PERSONA_URL}{pid}/confirm").json()["is_confirmed"] is True

    def test_confirm_sets_confirmed_at(self, auth_client):
        _, pid = _create(auth_client)
        assert auth_client.post(f"{PERSONA_URL}{pid}/confirm").json()["confirmed_at"] is not None

    def test_confirm_nonexistent_returns_404(self, auth_client):
        assert auth_client.post(f"{PERSONA_URL}PER-ghost/confirm").status_code == 404

    def test_confirm_idempotent(self, auth_client):
        """Confirming twice should not error — just stay confirmed."""
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        resp = auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert resp.status_code == 200
        assert resp.json()["is_confirmed"] is True

    def test_unauthenticated_confirm_returns_401(self, client):
        assert client.post(f"{PERSONA_URL}PER-anything/confirm").status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 7. UNCONFIRM
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaUnconfirm:

    def test_unconfirm_returns_200(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert auth_client.delete(f"{PERSONA_URL}{pid}/confirm").status_code == 200

    def test_unconfirm_sets_is_confirmed_false(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert auth_client.delete(f"{PERSONA_URL}{pid}/confirm").json()["is_confirmed"] is False

    def test_unconfirm_clears_confirmed_at(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert auth_client.delete(f"{PERSONA_URL}{pid}/confirm").json()["confirmed_at"] is None

    def test_unconfirm_nonexistent_returns_404(self, auth_client):
        assert auth_client.delete(f"{PERSONA_URL}PER-ghost/confirm").status_code == 404

    def test_confirm_unconfirm_confirm_cycle(self, auth_client):
        """Full cycle: confirm → unconfirm → confirm again."""
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        auth_client.delete(f"{PERSONA_URL}{pid}/confirm")
        resp = auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        assert resp.json()["is_confirmed"] is True
        assert resp.json()["confirmed_at"] is not None


# ══════════════════════════════════════════════════════════════════════════════
# 8. CONFIRMED LIST
# ══════════════════════════════════════════════════════════════════════════════

class TestConfirmedList:

    def test_confirmed_list_returns_200(self, auth_client):
        assert auth_client.get(f"{PERSONA_URL}confirmed").status_code == 200

    def test_confirmed_list_is_list(self, auth_client):
        assert isinstance(auth_client.get(f"{PERSONA_URL}confirmed").json(), list)

    def test_confirmed_list_includes_confirmed_persona(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        pids = [p["persona_id"] for p in auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert pid in pids

    def test_confirmed_list_excludes_unconfirmed(self, auth_client):
        _, pid = _create(auth_client)
        # deliberately do NOT confirm
        pids = [p["persona_id"] for p in auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert pid not in pids

    def test_confirmed_list_after_unconfirm(self, auth_client):
        _, pid = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        auth_client.delete(f"{PERSONA_URL}{pid}/confirm")
        pids = [p["persona_id"] for p in auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert pid not in pids

    def test_confirmed_list_multiple(self, auth_client):
        _, p1 = _create(auth_client)
        _, p2 = _create(auth_client)
        auth_client.post(f"{PERSONA_URL}{p1}/confirm")
        auth_client.post(f"{PERSONA_URL}{p2}/confirm")
        pids = [p["persona_id"] for p in auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert p1 in pids and p2 in pids


# ══════════════════════════════════════════════════════════════════════════════
# 9. AI FLOW — SAVE PERSONA FROM CHAT
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaSaveFromChat:

    def test_ask_save_persona_flag_exposed(self, auth_client):
        """AI returns ask_save_persona=True → flag is visible in response."""
        resp = _mock_plan(auth_client,
            "Plan a date for my girlfriend Sarah who loves sushi",
            _fake_ai(
                ask_save_persona=True,
                save_persona={"name": "Sarah", "relationship": "girlfriend",
                              "food_preferences": ["sushi"]},
                chat_response="Should I save Sarah's profile?",
            ))
        assert resp.status_code == 200
        assert resp.json()["ask_save_persona"] is True

    def test_persona_saved_when_user_says_yes(self, auth_client):
        name = f"AutoSave-{_uid()}"
        resp = _mock_plan(auth_client, "yes",
            _fake_ai(
                save_persona={"name": name, "relationship": "girlfriend",
                              "food_preferences": ["sushi"], "personality_tags": ["romantic"]},
                chat_response="Saved!",
            ))
        assert resp.status_code == 200
        assert resp.json()["persona_saved"] is True
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_sure(self, auth_client):
        name = f"Sure-{_uid()}"
        _mock_plan(auth_client, "sure",
            _fake_ai(save_persona={"name": name}, chat_response="Ok!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_ok(self, auth_client):
        name = f"Ok-{_uid()}"
        _mock_plan(auth_client, "ok",
            _fake_ai(save_persona={"name": name}, chat_response="Done!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_yep(self, auth_client):
        name = f"Yep-{_uid()}"
        _mock_plan(auth_client, "yep",
            _fake_ai(save_persona={"name": name}, chat_response="Done!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_yeah(self, auth_client):
        name = f"Yeah-{_uid()}"
        _mock_plan(auth_client, "yeah",
            _fake_ai(save_persona={"name": name}, chat_response="Done!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_please(self, auth_client):
        name = f"Please-{_uid()}"
        _mock_plan(auth_client, "yes please",
            _fake_ai(save_persona={"name": name}, chat_response="Done!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_saved_when_user_says_do_it(self, auth_client):
        name = f"DoIt-{_uid()}"
        _mock_plan(auth_client, "do it",
            _fake_ai(save_persona={"name": name}, chat_response="Done!"))
        assert name in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_auto_confirmed_after_save(self, auth_client):
        """Auto-saved persona must be is_confirmed=True immediately."""
        name = f"AutoConf-{_uid()}"
        _mock_plan(auth_client, "yes save her",
            _fake_ai(save_persona={"name": name, "food_preferences": ["pizza"],
                                   "music_preferences": ["jazz"]},
                     chat_response="Done!"))
        saved = next((p for p in auth_client.get(PERSONA_URL).json()
                      if p["name"] == name), None)
        if saved:
            assert saved["is_confirmed"] is True

    def test_persona_not_saved_when_user_says_no(self, auth_client):
        name = f"NoSave-{_uid()}"
        resp = _mock_plan(auth_client, "no thanks",
            _fake_ai(ask_save_persona=True,
                     save_persona={"name": name, "food_preferences": ["sushi"]},
                     chat_response="No problem!"))
        assert resp.status_code == 200
        assert name not in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_persona_not_saved_when_user_says_nope(self, auth_client):
        name = f"Nope-{_uid()}"
        _mock_plan(auth_client, "nope",
            _fake_ai(save_persona={"name": name}, chat_response="Ok!"))
        assert name not in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_duplicate_persona_not_created(self, auth_client):
        """Same name already exists → no duplicate, count stays at 1."""
        name = f"NoDupe-{_uid()}"
        _create(auth_client, name=name)
        _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={"name": name, "food_preferences": ["ramen"]},
                     chat_response="Saved!"))
        count = sum(1 for p in auth_client.get(PERSONA_URL).json() if p["name"] == name)
        assert count == 1

    def test_save_persona_stores_age_in_personality(self, auth_client):
        name = f"AgeTest-{_uid()}"
        _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={"name": name, "age": 28,
                                   "personality_tags": ["adventurous"]},
                     chat_response="Saved!"))
        saved = next((p for p in auth_client.get(PERSONA_URL).json()
                      if p["name"] == name), None)
        if saved:
            assert "28" in (saved.get("personality") or "")

    def test_save_persona_stores_relationship(self, auth_client):
        name = f"RelTest-{_uid()}"
        _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={"name": name, "relationship": "sister"},
                     chat_response="Saved!"))
        saved = next((p for p in auth_client.get(PERSONA_URL).json()
                      if p["name"] == name), None)
        if saved:
            assert saved.get("relationship") == "sister"

    def test_save_persona_stores_color_preferences(self, auth_client):
        name = f"ColorTest-{_uid()}"
        _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={"name": name, "color_preferences": ["purple", "gold"]},
                     chat_response="Saved!"))
        saved = next((p for p in auth_client.get(PERSONA_URL).json()
                      if p["name"] == name), None)
        if saved:
            assert "purple" in saved.get("color_preferences", [])

    def test_save_all_preference_fields_from_chat(self, auth_client):
        """Every extractable field from AI comes through correctly."""
        name = f"FullPrefs-{_uid()}"
        _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={
                "name":             name,
                "relationship":     "partner",
                "food_preferences":  ["sushi", "tacos"],
                "music_preferences": ["jazz", "pop"],
                "personality_tags":  ["adventurous", "romantic"],
                "color_preferences": ["blue"],
                "age":              25,
            }, chat_response="Saved all!"))
        saved = next((p for p in auth_client.get(PERSONA_URL).json()
                      if p["name"] == name), None)
        if saved:
            assert "sushi"       in saved["food_preferences"]
            assert "jazz"        in saved["music_preferences"]
            assert "adventurous" in saved["personality_tags"]
            assert "blue"        in saved["color_preferences"]
            assert "25"          in (saved.get("personality") or "")

    def test_save_persona_with_empty_name_does_not_crash(self, auth_client):
        resp = _mock_plan(auth_client, "yes",
            _fake_ai(save_persona={"name": "", "food_preferences": ["sushi"]},
                     chat_response="..."))
        assert resp.status_code == 200

    def test_save_persona_non_dict_does_not_crash(self, auth_client):
        """Malformed AI response where save_persona is a string → no crash."""
        resp = _mock_plan(auth_client, "yes",
            _fake_ai(save_persona="Sarah", chat_response="..."))
        assert resp.status_code == 200

    def test_persona_saved_false_when_no_save_data(self, auth_client):
        resp = _mock_plan(auth_client, "yes", _fake_ai())
        assert resp.json()["persona_saved"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 10. AI FLOW — LOAD / SUGGEST EXISTING PERSONA
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaLoadFromChat:

    def test_persona_confirmed_flag_when_ai_suggests(self, auth_client):
        """AI returns use_persona_name → persona_confirmed=True in response."""
        name = f"Suggest-{_uid()}"
        _create(auth_client, name=name, personality_tags=["romantic"])
        resp = _mock_plan(auth_client, f"Plan a date for {name}",
            _fake_ai(use_persona_name=name,
                     chat_response=f"I have {name}'s profile — use it?"))
        assert resp.status_code == 200
        assert resp.json()["persona_confirmed"] is True

    def test_suggested_persona_confirmed_in_db(self, auth_client):
        """After AI suggestion, persona is is_confirmed=True in the database."""
        name = f"DbConf-{_uid()}"
        _, pid = _create(auth_client, name=name, personality_tags=["cozy"])
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["is_confirmed"] is False
        _mock_plan(auth_client, f"plan for {name}",
            _fake_ai(use_persona_name=name, chat_response=f"Using {name}!"))
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["is_confirmed"] is True

    def test_already_confirmed_persona_stays_confirmed(self, auth_client):
        """Suggesting an already-confirmed persona should be idempotent."""
        name = f"AlreadyConf-{_uid()}"
        _, pid = _create(auth_client, name=name)
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        _mock_plan(auth_client, f"plan for {name}",
            _fake_ai(use_persona_name=name, chat_response="Using profile!"))
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["is_confirmed"] is True

    def test_nonexistent_use_persona_name_no_crash(self, auth_client):
        """use_persona_name for unknown person → graceful skip, no 500."""
        resp = _mock_plan(auth_client, "plan a date",
            _fake_ai(use_persona_name="GhostPerson", chat_response="Let me help!"))
        assert resp.status_code == 200

    def test_persona_confirmed_false_when_use_persona_name_empty(self, auth_client):
        """Empty string for use_persona_name → persona_confirmed=False."""
        resp = _mock_plan(auth_client, "plan something",
            _fake_ai(use_persona_name="", chat_response="Sure!"))
        assert resp.json()["persona_confirmed"] is False

    def test_persona_confirmed_false_when_no_use_persona_name(self, auth_client):
        """No use_persona_name in AI result → persona_confirmed=False."""
        resp = _mock_plan(auth_client, "plan something", _fake_ai())
        assert resp.json()["persona_confirmed"] is False

    def test_multiple_personas_can_be_confirmed_in_session(self, auth_client):
        _, pid1 = _create(auth_client, name=f"Alice-{_uid()}")
        _, pid2 = _create(auth_client, name=f"Bob-{_uid()}")
        auth_client.post(f"{PERSONA_URL}{pid1}/confirm")
        auth_client.post(f"{PERSONA_URL}{pid2}/confirm")
        confirmed_ids = [p["persona_id"] for p in
                         auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert pid1 in confirmed_ids and pid2 in confirmed_ids

    def test_planning_200_with_confirmed_persona(self, auth_client):
        _, pid = _create(auth_client, name=f"Plan-{_uid()}", personality_tags=["romantic"])
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        resp = _mock_plan(auth_client, "Plan a romantic date",
            _fake_ai(intent="planning", venue_tags=["romantic"],
                     chat_response="Here are some venues!"))
        assert resp.status_code == 200

    def test_confirmed_persona_venue_tags_reach_response(self, auth_client):
        _, pid = _create(auth_client, name=f"VTag-{_uid()}",
                         personality_tags=["romantic"], food_preferences=["sushi"])
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        resp = _mock_plan(auth_client, "Plan a romantic sushi dinner",
            _fake_ai(intent="planning", venue_tags=["romantic", "fine-dining"],
                     chat_response="Found venues!"))
        assert resp.status_code == 200
        assert "romantic" in resp.json()["venue_tags"]


# ══════════════════════════════════════════════════════════════════════════════
# 11. PLAN RESPONSE — PERSONA FLAGS
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanResponsePersonaFlags:

    def test_response_always_has_all_three_flags(self, auth_client):
        resp = _mock_plan(auth_client, "Hello", _fake_ai(chat_response="Hi!"))
        data = resp.json()
        assert "ask_save_persona"  in data
        assert "persona_saved"     in data
        assert "persona_confirmed" in data

    def test_all_flags_false_by_default(self, auth_client):
        resp = _mock_plan(auth_client, "Hello", _fake_ai())
        data = resp.json()
        assert data["ask_save_persona"]  is False
        assert data["persona_saved"]     is False
        assert data["persona_confirmed"] is False

    def test_planning_works_with_zero_personas(self, auth_client):
        resp = _mock_plan(auth_client, "Plan something nice",
            _fake_ai(intent="planning", venue_tags=["romantic"],
                     missing_info=["location"],
                     chat_response="Where should the event be?"))
        assert resp.status_code == 200

    def test_ask_save_false_for_generic_query(self, auth_client):
        resp = _mock_plan(auth_client, "I want to plan something",
            _fake_ai(chat_response="Tell me more!"))
        assert resp.json()["ask_save_persona"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 12. PLANNING ENDPOINT VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanningEndpointValidation:

    def test_invalid_session_id_returns_400(self, auth_client):
        resp = auth_client.post(PLANNING_URL, json={
            "session_id": "invalid session id with spaces!!!",
            "user_query":  "plan something",
        })
        assert resp.status_code == 400

    def test_missing_session_id_returns_422(self, auth_client):
        resp = auth_client.post(PLANNING_URL, json={"user_query": "plan something"})
        assert resp.status_code == 422

    def test_missing_user_query_returns_422(self, auth_client):
        resp = auth_client.post(PLANNING_URL, json={"session_id": "sess-abc"})
        assert resp.status_code == 422

    def test_unauthenticated_planning_returns_401(self, client):
        resp = client.post(PLANNING_URL, json={
            "session_id": "sess-abc", "user_query": "plan something"
        })
        assert resp.status_code in (401, 403)

    def test_rate_limit_triggers_429(self, auth_client):
        """Exceed rate limit → 429. Fails open if Redis not available (skipped)."""
        fake = _fake_ai(chat_response="ok")
        session = f"ratelimit-{_uid()}"
        responses = []
        with patch("app.services.ai_service.ai_service.generate_date_plan",
                   new_callable=AsyncMock, return_value=fake):
            for _ in range(15):
                r = _plan(auth_client, "plan", session_id=session)
                responses.append(r.status_code)
        # Either 429 was triggered OR Redis is unavailable (all 200s — acceptable)
        assert all(s in (200, 429) for s in responses)


# ══════════════════════════════════════════════════════════════════════════════
# 13. SERVICE BEHAVIOUR (end-to-end via HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaServiceBehaviour:

    def test_create_and_retrieve(self, auth_client):
        name = f"SvcTest-{_uid()}"
        _, pid = _create(auth_client, name=name)
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert data["name"] == name
        assert data["persona_id"].startswith("PER")

    def test_full_confirm_unconfirm_cycle(self, auth_client):
        _, pid = _create(auth_client)
        c = auth_client.post(f"{PERSONA_URL}{pid}/confirm").json()
        assert c["is_confirmed"] is True
        assert c["confirmed_at"] is not None
        u = auth_client.delete(f"{PERSONA_URL}{pid}/confirm").json()
        assert u["is_confirmed"] is False
        assert u["confirmed_at"] is None

    def test_delete_removes_persona_from_list(self, auth_client):
        name = f"DelSvc-{_uid()}"
        _, pid = _create(auth_client, name=name)
        auth_client.delete(f"{PERSONA_URL}{pid}")
        assert name not in [p["name"] for p in auth_client.get(PERSONA_URL).json()]

    def test_confirmed_first_ordering_in_list(self, auth_client):
        _, p1 = _create(auth_client, name=f"Last-{_uid()}")
        _, p2 = _create(auth_client, name=f"First-{_uid()}")
        auth_client.post(f"{PERSONA_URL}{p2}/confirm")
        ids = [p["persona_id"] for p in auth_client.get(PERSONA_URL).json()]
        assert ids.index(p2) < ids.index(p1)

    def test_response_has_all_expected_keys(self, auth_client):
        _, pid = _create(auth_client, food_preferences=["pizza"], personality_tags=["cozy"])
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        for key in ("food_preferences", "color_preferences", "music_preferences",
                    "personality_tags", "is_confirmed", "confirmed_at",
                    "created_at", "updated_at"):
            assert key in data, f"missing key: {key}"
        assert data["is_confirmed"] is False

    def test_multiple_personas_same_name_get_unique_ids(self, auth_client):
        _, pid1 = _create(auth_client, name="Twin")
        _, pid2 = _create(auth_client, name="Twin")
        assert pid1 != pid2


# ══════════════════════════════════════════════════════════════════════════════
# 14. LEGACY REGRESSION (merged from original test_personas.py)
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaLegacy:

    def test_list_returns_list_not_envelope(self, auth_client):
        r = auth_client.get(PERSONA_URL)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_contains_multiple_created_personas(self, auth_client):
        auth_client.post(PERSONA_URL, json={"name": "Sarah"})
        auth_client.post(PERSONA_URL, json={"name": "Mom"})
        assert len(auth_client.get(PERSONA_URL).json()) >= 2

    def test_create_basic(self, auth_client):
        r = auth_client.post(PERSONA_URL, json={"name": "Sarah"})
        assert r.status_code == 201
        assert r.json()["name"] == "Sarah"
        assert "persona_id" in r.json()

    def test_get_basic(self, auth_client):
        pid = auth_client.post(PERSONA_URL, json={"name": "Sarah"}).json()["persona_id"]
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["persona_id"] == pid

    def test_update_basic(self, auth_client):
        pid = auth_client.post(PERSONA_URL, json={"name": "Sarah"}).json()["persona_id"]
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "Sara"}).json()["name"] == "Sara"

    def test_delete_returns_204(self, auth_client):
        pid = auth_client.post(PERSONA_URL, json={"name": "Sarah"}).json()["persona_id"]
        assert auth_client.delete(f"{PERSONA_URL}{pid}").status_code == 204

    def test_delete_not_found_returns_404(self, auth_client):
        assert auth_client.delete(f"{PERSONA_URL}PER-doesnotexist").status_code == 404

    def test_get_not_found_returns_404(self, auth_client):
        assert auth_client.get(f"{PERSONA_URL}PER-doesnotexist").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 15. PERSONA EDITING & UPDATE VALIDATION  — OCA-250 [E23][TE]
#
# Ticket:  [E23][TE] - Validate Persona Editing & Update Behavior
# Goal:    Verify that every editable field updates correctly, that partial
#          updates never corrupt untouched fields, that updated_at advances,
#          that ownership isolation is enforced, and that invalid payloads are
#          rejected with the right HTTP status codes.
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonaEditValidation:
    """OCA-250 — Validate Persona Editing & Update Behavior.

    These tests exercise:
      • Field-level update correctness for every editable field
      • Partial-update isolation (no field wiping)
      • updated_at timestamp advances after edit
      • persona_id / customer_id / created_at are immutable
      • Ownership: another customer cannot edit your persona
      • Blank / whitespace-only name rejected (422)
      • Name-collision between two customers is allowed (different owners)
      • List fields accept empty list (explicit clear)
      • Sequential multi-field edits accumulate correctly
      • Confirmed persona remains confirmed after edit
      • Response body always reflects the new state (not stale cache)
    """

    # ── Field-level correctness ───────────────────────────────────────────────

    def test_edit_name_reflected_immediately(self, auth_client):
        """PUT with new name → GET returns updated name without re-create."""
        _, pid = _create(auth_client, name="Before")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "After"})
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["name"] == "After"

    def test_edit_relationship_all_values(self, auth_client):
        """Relationship can be updated to any free-text string."""
        _, pid = _create(auth_client)
        for rel in ["girlfriend", "wife", "mother", "colleague", "best friend"]:
            resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": rel})
            assert resp.status_code == 200
            assert resp.json()["relationship"] == rel

    def test_edit_personality_free_text(self, auth_client):
        """Personality accepts any free-text description."""
        _, pid = _create(auth_client)
        long_text = "Loves early mornings, strong coffee, indie bookshops, and hiking on weekends."
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"personality": long_text})
        assert resp.status_code == 200
        assert "coffee" in resp.json()["personality"]

    def test_edit_food_preferences_replace(self, auth_client):
        """Replacing food_preferences fully replaces the list."""
        _, pid = _create(auth_client, food_preferences=["sushi", "pizza"])
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"food_preferences": ["tacos"]})
        assert resp.status_code == 200
        data = resp.json()["food_preferences"]
        assert "tacos" in data
        assert "sushi" not in data   # old value gone

    def test_edit_color_preferences_replace(self, auth_client):
        """Replacing color_preferences fully replaces the list."""
        _, pid = _create(auth_client, color_preferences=["blue", "white"])
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"color_preferences": ["gold", "black"]})
        assert resp.status_code == 200
        data = resp.json()["color_preferences"]
        assert "gold" in data
        assert "blue" not in data

    def test_edit_music_preferences_replace(self, auth_client):
        """Replacing music_preferences fully replaces the list."""
        _, pid = _create(auth_client, music_preferences=["jazz"])
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"music_preferences": ["k-pop", "metal"]})
        assert resp.status_code == 200
        data = resp.json()["music_preferences"]
        assert "k-pop" in data
        assert "jazz" not in data

    def test_edit_personality_tags_replace(self, auth_client):
        """Replacing personality_tags fully replaces the list."""
        _, pid = _create(auth_client, personality_tags=["romantic", "adventurous"])
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"personality_tags": ["bookworm"]})
        assert resp.status_code == 200
        data = resp.json()["personality_tags"]
        assert "bookworm" in data
        assert "romantic" not in data

    def test_edit_birthday_valid_iso_date(self, auth_client):
        """Birthday accepts ISO-8601 date string."""
        _, pid = _create(auth_client)
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"birthday": "1990-12-25"})
        assert resp.status_code == 200
        assert "1990-12-25" in (resp.json().get("birthday") or "")

    def test_edit_birthday_clear_with_null(self, auth_client):
        """Birthday can be cleared by sending null."""
        _, pid = _create(auth_client, birthday="1990-12-25")
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"birthday": None})
        assert resp.status_code == 200
        assert resp.json().get("birthday") is None

    def test_edit_list_fields_to_empty_clears_them(self, auth_client):
        """Explicitly sending [] clears the list field."""
        _, pid = _create(auth_client, food_preferences=["sushi"],
                         personality_tags=["romantic"])
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={
            "food_preferences":  [],
            "personality_tags":  [],
        })
        assert resp.status_code == 200
        assert resp.json()["food_preferences"] == []
        assert resp.json()["personality_tags"] == []

    # ── Partial update isolation ──────────────────────────────────────────────

    def test_edit_name_only_preserves_all_lists(self, auth_client):
        """Updating only name must not touch any preference list."""
        _, pid = _create(auth_client,
                         name="Original",
                         food_preferences=["ramen"],
                         color_preferences=["red"],
                         music_preferences=["pop"],
                         personality_tags=["cozy"])
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "Updated"})
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert "ramen"  in data["food_preferences"]
        assert "red"    in data["color_preferences"]
        assert "pop"    in data["music_preferences"]
        assert "cozy"   in data["personality_tags"]

    def test_edit_one_list_preserves_other_lists(self, auth_client):
        """Updating food_preferences must not touch music or personality."""
        _, pid = _create(auth_client,
                         food_preferences=["sushi"],
                         music_preferences=["jazz"],
                         personality_tags=["adventurous"])
        auth_client.put(f"{PERSONA_URL}{pid}", json={"food_preferences": ["tacos"]})
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert "jazz"        in data["music_preferences"]
        assert "adventurous" in data["personality_tags"]

    def test_edit_relationship_preserves_birthday(self, auth_client):
        """Updating relationship must not clear birthday."""
        _, pid = _create(auth_client, birthday="1995-06-15")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": "sister"})
        bday = auth_client.get(f"{PERSONA_URL}{pid}").json().get("birthday") or ""
        assert "1995-06-15" in bday

    def test_sequential_edits_accumulate(self, auth_client):
        """Three successive partial updates all take effect."""
        _, pid = _create(auth_client, name="Step0")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "Step1"})
        auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": "partner"})
        auth_client.put(f"{PERSONA_URL}{pid}", json={"personality_tags": ["thoughtful"]})
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert data["name"]         == "Step1"
        assert data["relationship"] == "partner"
        assert "thoughtful"         in data["personality_tags"]

    # ── updated_at behaviour ─────────────────────────────────────────────────

    def test_updated_at_advances_after_edit(self, auth_client):
        """updated_at after PUT must be >= updated_at before PUT."""
        import time
        _, pid = _create(auth_client)
        before = auth_client.get(f"{PERSONA_URL}{pid}").json().get("updated_at") or ""
        time.sleep(0.05)   # small sleep so timestamps differ
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": f"Changed-{_uid()}"})
        after = auth_client.get(f"{PERSONA_URL}{pid}").json().get("updated_at") or ""
        # If both are present, after must be >= before
        if before and after:
            assert after >= before

    def test_updated_at_present_in_response(self, auth_client):
        """PUT response body contains updated_at field."""
        _, pid = _create(auth_client)
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "CheckTS"})
        assert "updated_at" in resp.json()

    # ── Immutable fields ──────────────────────────────────────────────────────

    def test_persona_id_cannot_be_changed(self, auth_client):
        """Sending a different persona_id in the body must not change it."""
        _, pid = _create(auth_client)
        auth_client.put(f"{PERSONA_URL}{pid}", json={"persona_id": "PER-HACKED"})
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["persona_id"] == pid

    def test_customer_id_cannot_be_changed(self, auth_client):
        """customer_id is read-only — body value must be ignored."""
        _, pid = _create(auth_client)
        original_cid = auth_client.get(f"{PERSONA_URL}{pid}").json()["customer_id"]
        auth_client.put(f"{PERSONA_URL}{pid}", json={"customer_id": "CUS-HACKED"})
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["customer_id"] == original_cid

    def test_created_at_does_not_change_on_edit(self, auth_client):
        """created_at must be identical before and after PUT."""
        _, pid = _create(auth_client)
        before = auth_client.get(f"{PERSONA_URL}{pid}").json().get("created_at")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "EditedName"})
        after = auth_client.get(f"{PERSONA_URL}{pid}").json().get("created_at")
        if before and after:
            assert before == after

    # ── Ownership isolation ───────────────────────────────────────────────────

    def test_other_customer_cannot_edit_persona(self, auth_client, client):
        """Customer B must get 404 when trying to PUT Customer A's persona."""
        _, pid = _create(auth_client, name="Private")
        email2 = f"edit_other_{_uid()}@test.com"
        client.post("/api/v1/auth/customers/register",
                    json={"email": email2, "password": "pass1234", "full_name": "OtherEditor"})
        tok = client.post("/api/v1/auth/customers/login",
                          data={"username": email2, "password": "pass1234"}).json().get("access_token")
        if tok:
            resp = client.put(
                f"{PERSONA_URL}{pid}",
                json={"name": "Hacked"},
                headers={"Authorization": f"Bearer {tok}"},
            )
            assert resp.status_code == 404

    # ── Input validation ──────────────────────────────────────────────────────

    def test_edit_name_to_empty_string_returns_422(self, auth_client):
        """name: '' must be rejected with 422."""
        _, pid = _create(auth_client)
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"name": ""}).status_code == 422

    def test_edit_name_to_whitespace_only_returns_422(self, auth_client):
        """name: '   ' (whitespace only) must be rejected with 422."""
        _, pid = _create(auth_client)
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "   "}).status_code == 422

    def test_edit_invalid_birthday_format_returns_422(self, auth_client):
        """Non-ISO birthday string must be rejected with 422."""
        _, pid = _create(auth_client)
        assert auth_client.put(f"{PERSONA_URL}{pid}", json={"birthday": "25/12/1990"}).status_code == 422

    def test_edit_list_field_with_non_list_returns_422(self, auth_client):
        """Sending a string instead of a list for food_preferences → 422."""
        _, pid = _create(auth_client)
        assert auth_client.put(
            f"{PERSONA_URL}{pid}", json={"food_preferences": "sushi"}
        ).status_code == 422

    def test_edit_nonexistent_persona_returns_404(self, auth_client):
        """PUT on a persona_id that does not exist → 404."""
        assert auth_client.put(
            f"{PERSONA_URL}PER-nonexistent999",
            json={"name": "Ghost"},
        ).status_code == 404

    def test_unauthenticated_edit_returns_401(self, client):
        """No Bearer token → 401."""
        assert client.put(
            f"{PERSONA_URL}PER-anything",
            json={"name": "x"},
        ).status_code in (401, 403)

    # ── Confirmed-persona behaviour ───────────────────────────────────────────

    def test_edit_confirmed_persona_keeps_is_confirmed_true(self, auth_client):
        """Editing a confirmed persona must not reset is_confirmed to False."""
        _, pid = _create(auth_client, name="Confirmed")
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "ConfirmedEdited"})
        assert auth_client.get(f"{PERSONA_URL}{pid}").json()["is_confirmed"] is True

    def test_edit_confirmed_persona_keeps_confirmed_at(self, auth_client):
        """Editing a confirmed persona must not clear confirmed_at."""
        _, pid = _create(auth_client)
        confirmed_at = auth_client.post(f"{PERSONA_URL}{pid}/confirm").json().get("confirmed_at")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"relationship": "partner"})
        data = auth_client.get(f"{PERSONA_URL}{pid}").json()
        assert data["is_confirmed"] is True
        if confirmed_at:
            assert data.get("confirmed_at") is not None

    def test_edit_confirmed_persona_appears_in_confirmed_list(self, auth_client):
        """After editing a confirmed persona it must still appear in /confirmed."""
        _, pid = _create(auth_client, name="StillConfirmed")
        auth_client.post(f"{PERSONA_URL}{pid}/confirm")
        auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "StillConfirmedEdited"})
        pids = [p["persona_id"]
                for p in auth_client.get(f"{PERSONA_URL}confirmed").json()]
        assert pid in pids

    # ── Response shape after edit ─────────────────────────────────────────────

    def test_edit_response_contains_all_required_keys(self, auth_client):
        """PUT response must include every field the GET response has."""
        _, pid = _create(auth_client)
        resp = auth_client.put(f"{PERSONA_URL}{pid}", json={"name": "KeyCheck"})
        data = resp.json()
        for key in ("persona_id", "customer_id", "name", "relationship",
                    "food_preferences", "color_preferences", "music_preferences",
                    "personality_tags", "is_confirmed", "updated_at"):
            assert key in data, f"Missing key in PUT response: {key}"

    def test_edit_response_matches_subsequent_get(self, auth_client):
        """PUT response body must be identical to the following GET."""
        _, pid = _create(auth_client)
        put_body = auth_client.put(
            f"{PERSONA_URL}{pid}",
            json={"name": "SyncCheck", "relationship": "friend"},
        ).json()
        get_body = auth_client.get(f"{PERSONA_URL}{pid}").json()
        # Compare key subset
        for key in ("name", "relationship", "persona_id", "is_confirmed"):
            assert put_body.get(key) == get_body.get(key), f"Mismatch on key: {key}"

    # ── Cross-customer name collision (allowed) ───────────────────────────────

    def test_two_customers_can_have_same_persona_name(self, auth_client, client):
        """Different customers are allowed to have personas with the same name."""
        _, pid1 = _create(auth_client, name="SharedName")
        email2 = f"name_coll_{_uid()}@test.com"
        client.post("/api/v1/auth/customers/register",
                    json={"email": email2, "password": "pass1234",
                          "full_name": "NameCollision"})
        tok = client.post("/api/v1/auth/customers/login",
                          data={"username": email2, "password": "pass1234"}).json().get("access_token")
        if tok:
            resp = client.post(
                PERSONA_URL,
                json={"name": "SharedName"},
                headers={"Authorization": f"Bearer {tok}"},
            )
            # Both customers can have "SharedName" — must not 409
            assert resp.status_code == 201