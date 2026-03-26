from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.admin import Admin


def _create_admin() -> Admin:
    db = SessionLocal()
    admin = Admin(
        admin_id=f"ADM-{uuid4().hex[:16]}",
        email=f"admin-{uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("AdminPass123!"),
        staff_role="staff",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


def test_admin_verify_otp_requires_redis(client):
    admin = _create_admin()
    with patch("app.services.admin_service._get_redis", return_value=None):
        r = client.post(
            "/api/v1/auth/admin/login/verify-otp",
            json={"email": admin.email, "otp": "123456"},
        )
    assert r.status_code == 503
