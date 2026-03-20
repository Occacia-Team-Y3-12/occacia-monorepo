# ruff: noqa: S101
"""
tests/Unit/test_auth_service_links.py

Ensures that the authentication service generates the correct frontend URLs
in its plain-text email templates.
"""

from app.services.auth_service import (
    _build_customer_verification_email,
    _build_password_reset_email,
    _build_vendor_verification_email,
)


def test_customer_verification_email_uses_frontend_path():
    """Ensure customer verification emails point to the Next.js app."""
    token = "test-verification-token"
    _, body = _build_customer_verification_email("user@test.com", token)

    assert f"https://app.occacia.com/customers/register/verify-email?token={token}" in body
    assert "/api/v1/auth" not in body


def test_customer_password_reset_email_uses_frontend_path():
    """Ensure password reset emails point to the Next.js app."""
    token = "test-reset-token"
    _, body = _build_password_reset_email("user@test.com", token)

    assert f"https://app.occacia.com/reset-password?token={token}" in body
    assert "/api/v1/auth" not in body


def test_vendor_verification_email_uses_frontend_path():
    """Ensure vendor verification emails point to the Next.js app."""
    token = "test-vendor-token"
    _, body = _build_vendor_verification_email("vendor@test.com", token)

    assert f"https://app.occacia.com/vendor-verify?token={token}" in body
    assert "/api/v1/auth" not in body
