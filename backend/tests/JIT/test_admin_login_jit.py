from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import get_password_hash
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


def _create_admin() -> Admin:
    db = SessionLocal()
    admin = Admin(
        admin_id=f"ADM-{uuid4().hex[:12]}",
        email=f"jit-admin-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("AdminPass123!"),
        staff_role="staff",
        email_verified=True,
        status="ACTIVE",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def test_admin_login_otp_jit(client):
    admin = _create_admin()
    fake_redis = _FakeRedis()
    with patch("app.services.admin_service._get_redis", return_value=fake_redis):
        login = client.post(
            "/api/v1/auth/admin/login",
            json={"email": admin.email, "password": "AdminPass123!"},
        )
        assert login.status_code == 200

        otp_code = fake_redis.get(f"admin_otp:{admin.admin_id}")
        assert otp_code

        verify = client.post(
            "/api/v1/auth/admin/login/verify-otp",
            json={"email": admin.email, "otp": otp_code},
        )
        assert verify.status_code == 200
        assert "accessToken" in verify.json()
