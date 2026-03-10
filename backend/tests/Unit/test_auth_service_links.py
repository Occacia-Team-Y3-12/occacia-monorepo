# ruff: noqa: S101

from app.services.auth_service import (
    _build_customer_verification_email,
    _build_password_reset_email,
)


def test_customer_verification_email_uses_singular_auth_path():
    token = "test-verification-token"

    _, html = _build_customer_verification_email("user@test.com", token)

    assert "/api/v1/auth/customer/verify-email?token=test-verification-token" in html
    assert "/api/v1/auth/customers/verify-email" not in html


def test_customer_password_reset_email_uses_singular_auth_path():
    token = "test-reset-token"

    _, html = _build_password_reset_email("user@test.com", token)

    assert "/api/v1/auth/customer/password/reset?token=test-reset-token" in html
    assert "/api/v1/auth/customers/reset-password" not in html
