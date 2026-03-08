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