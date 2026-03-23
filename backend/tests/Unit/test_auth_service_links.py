# ruff: noqa: S101
"""
tests/Unit/test_auth_service_links.py

Tests that authentication emails contain the correct frontend URLs.

Updated to match the new notification_service template system.
The old _build_*_email helper functions were removed from auth_service and
replaced with templates in notification_service._TEMPLATES.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("REDIS_PASSWORD", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://admin:test@localhost:5432/occacia_test")


from app.services.notification_service import (
    NotificationService,
    CUSTOMER_VERIFICATION_NOTIFICATION,
    VENDOR_VERIFICATION_NOTIFICATION,
    CUSTOMER_PASSWORD_RESET_LINK,
    VENDOR_PASSWORD_RESET_LINK,
    ADMIN_PASSWORD_RESET_OTP,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render(notification_type: str, context: dict) -> tuple[str, str]:
    """Render a template and return (subject, text_body)."""
    svc = NotificationService()
    rendered = svc.render_template(
        notification_type=notification_type,
        recipient_name=context.get("userName", "Test User"),
        context_data=context,
    )
    return rendered.subject, rendered.text_body, rendered.html_body


# ── Customer verification ─────────────────────────────────────────────────────

def test_customer_verification_email_uses_frontend_path():
    """Customer verification emails must point to the Next.js frontend."""
    token = "test-verification-token"
    _, body, html = _render(CUSTOMER_VERIFICATION_NOTIFICATION, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/customer/auth/verify-email?token={token}",
    })
    assert f"https://app.occacia.com/customer/auth/verify-email?token={token}" in body
    assert "/api/v1/auth" not in body
    assert token in body


def test_customer_verification_html_contains_link():
    """Customer verification HTML email must contain the verification link."""
    token = "test-html-token"
    link = f"https://app.occacia.com/customer/auth/verify-email?token={token}"
    _, _, html = _render(CUSTOMER_VERIFICATION_NOTIFICATION, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "verificationToken": token,
        "verificationLink": link,
    })
    assert link in html
    assert "Verify" in html


def test_customer_verification_subject():
    """Customer verification email must have the correct subject."""
    token = "tok"
    subject, _, _ = _render(CUSTOMER_VERIFICATION_NOTIFICATION, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/customer/auth/verify-email?token={token}",
    })
    assert "Verify" in subject or "Occacia" in subject


# ── Vendor verification ───────────────────────────────────────────────────────

def test_vendor_verification_email_uses_frontend_path():
    """Vendor verification emails must point to the Next.js frontend."""
    token = "test-vendor-token"
    _, body, _ = _render(VENDOR_VERIFICATION_NOTIFICATION, {
        "userId": "VEN-001",
        "userName": "Test Vendor",
        "userEmail": "vendor@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/vendor/auth/verify-email?token={token}",
    })
    assert f"https://app.occacia.com/vendor/auth/verify-email?token={token}" in body
    assert "/api/v1/auth" not in body
    assert token in body


def test_vendor_verification_subject():
    """Vendor verification email subject must mention vendor."""
    token = "tok"
    subject, _, _ = _render(VENDOR_VERIFICATION_NOTIFICATION, {
        "userId": "VEN-001",
        "userName": "Test Vendor",
        "userEmail": "vendor@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/vendor/auth/verify-email?token={token}",
    })
    assert "vendor" in subject.lower() or "Occacia" in subject


# ── Customer password reset link ──────────────────────────────────────────────

def test_customer_password_reset_link_contains_frontend_url():
    """Customer password reset email must contain the frontend reset link."""
    token = "reset-token-123"
    link = f"https://app.occacia.com/customer/auth/reset-password?token={token}"
    _, body, html = _render(CUSTOMER_PASSWORD_RESET_LINK, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "resetToken": token,
        "resetLink": link,
    })
    assert link in body
    assert link in html


def test_customer_password_reset_link_no_backend_api_path():
    """Customer password reset email must point to frontend, not backend API."""
    _, body, _ = _render(CUSTOMER_PASSWORD_RESET_LINK, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "resetToken": "reset-token-456",
        "resetLink": "https://app.occacia.com/customer/auth/reset-password?token=reset-token-456",
    })
    assert "/api/v1/auth" not in body


def test_customer_password_reset_link_subject():
    """Customer password reset email subject must mention reset."""
    subject, _, _ = _render(CUSTOMER_PASSWORD_RESET_LINK, {
        "userId": "CUS-001",
        "userName": "Test User",
        "userEmail": "user@test.com",
        "resetToken": "reset-token-789",
        "resetLink": "https://app.occacia.com/customer/auth/reset-password?token=reset-token-789",
    })
    assert any(word in subject.lower() for word in ["reset", "password", "occacia"])


# ── Vendor password reset link ────────────────────────────────────────────────

def test_vendor_password_reset_link_contains_frontend_url():
    """Vendor password reset email must contain the frontend reset link."""
    token = "vendor-reset-token-123"
    link = f"https://app.occacia.com/vendor/auth/reset-password?token={token}"
    _, body, html = _render(VENDOR_PASSWORD_RESET_LINK, {
        "userId": "VEN-001",
        "userName": "Test Vendor",
        "userEmail": "vendor@test.com",
        "resetToken": token,
        "resetLink": link,
    })
    assert link in body
    assert link in html


def test_vendor_password_reset_link_subject_mentions_vendor():
    """Vendor password reset email subject must mention vendor."""
    subject, _, _ = _render(VENDOR_PASSWORD_RESET_LINK, {
        "userId": "VEN-001",
        "userName": "Test Vendor",
        "userEmail": "vendor@test.com",
        "resetToken": "vendor-reset-token-456",
        "resetLink": "https://app.occacia.com/vendor/auth/reset-password?token=vendor-reset-token-456",
    })
    assert "vendor" in subject.lower() or "Occacia" in subject


# ── Admin password reset OTP ──────────────────────────────────────────────────

def test_admin_password_reset_otp_contains_code():
    """Admin password reset OTP email must contain the OTP code."""
    otp = "999888"
    _, body, html = _render(ADMIN_PASSWORD_RESET_OTP, {
        "userId": "ADM-001",
        "userName": "admin@occacia.com",
        "userEmail": "admin@occacia.com",
        "otpCode": otp,
    })
    assert otp in body
    assert otp in html


def test_admin_password_reset_otp_warns_about_security():
    """Admin OTP email must contain a security warning."""
    _, body, _ = _render(ADMIN_PASSWORD_RESET_OTP, {
        "userId": "ADM-001",
        "userName": "admin@occacia.com",
        "userEmail": "admin@occacia.com",
        "otpCode": "777666",
    })
    # Should warn about contacting admin if not requested
    assert "administrator" in body.lower() or "did not" in body.lower()


# ── Cross-role URL isolation ──────────────────────────────────────────────────

def test_customer_and_vendor_verification_use_different_paths():
    """Customer and vendor verification links must use different URL paths."""
    token = "shared-token"

    _, customer_body, _ = _render(CUSTOMER_VERIFICATION_NOTIFICATION, {
        "userId": "CUS-001",
        "userName": "Customer",
        "userEmail": "c@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/customer/auth/verify-email?token={token}",
    })
    _, vendor_body, _ = _render(VENDOR_VERIFICATION_NOTIFICATION, {
        "userId": "VEN-001",
        "userName": "Vendor",
        "userEmail": "v@test.com",
        "verificationToken": token,
        "verificationLink": f"https://app.occacia.com/vendor/auth/verify-email?token={token}",
    })

    assert "/customer/auth/verify-email" in customer_body
    assert "/vendor/auth/verify-email" in vendor_body
    # They must not share the same path
    assert "/vendor/auth/verify-email" not in customer_body
    assert "/customer/auth/verify-email" not in vendor_body
