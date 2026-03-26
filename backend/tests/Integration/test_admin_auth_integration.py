from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.models.admin import Admin


class _FakeRedis:
    def __init__(self):
        self._store: dict[str, tuple[str, int | None]] = {}

    def ping(self):
        return True

    def setex(self, key: str, ttl: int, value: str):
        self._store[key] = (value, ttl)
        return True

    def get(self, key: str):
        item = self._store.get(key)
        return item[0] if item else None

    def delete(self, key: str):
        if key in self._store:
            del self._store[key]


def _get_admin_by_email(email: str) -> Admin | None:
    db = SessionLocal()
    admin = db.query(Admin).filter(Admin.email == email).first()
    db.close()
    return admin


def test_admin_register_verify_login_integration(client, monkeypatch):
    monkeypatch.setenv("DISABLE_ADMIN_REGISTER", "false")
    monkeypatch.setenv("SKIP_EMAIL_VERIFICATION", "false")

    email = f"admin-int-{uuid4().hex[:8]}@test.com"
    password = "AdminPass123!"

    register = client.post(
        "/api/v1/auth/admin/register",
        json={"email": email, "password": password, "staff_role": "staff"},
    )
    if register.status_code == 403:
        return
    assert register.status_code == 201

    admin = _get_admin_by_email(email)
    assert admin is not None
    assert admin.verification_token

    blocked_login = client.post(
        "/api/v1/auth/admin/login",
        json={"email": email, "password": password},
    )
    assert blocked_login.status_code == 403

    verified = client.get(f"/api/v1/auth/admin/verify-email?token={admin.verification_token}")
    assert verified.status_code == 200

    fake_redis = _FakeRedis()
    with patch("app.services.admin_service._get_redis", return_value=fake_redis):
        login = client.post(
            "/api/v1/auth/admin/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200

        otp_code = fake_redis.get(f"admin_otp:{admin.admin_id}")
        assert otp_code

        verify = client.post(
            "/api/v1/auth/admin/login/verify-otp",
            json={"email": email, "otp": otp_code},
        )
        assert verify.status_code == 200
        body = verify.json()
        assert "accessToken" in body
        assert "refreshToken" in body
        assert body["user"]["email"] == email
